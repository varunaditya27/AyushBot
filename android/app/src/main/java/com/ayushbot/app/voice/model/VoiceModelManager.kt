package com.ayushbot.app.voice.model

import android.content.Context
import com.ayushbot.app.core.config.AsrConfig
import com.ayushbot.app.core.config.TtsConfig
import com.ayushbot.app.core.config.VoiceConfig
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request

enum class VoiceModelType {
    ASR,
    TTS,
}

class VoiceModelManager(
    private val context: Context,
    private val voiceConfig: VoiceConfig,
    private val httpClient: OkHttpClient = OkHttpClient(),
) {
    private val baseDir: File = File(
        context.filesDir,
        voiceConfig.modelBaseDir.ifBlank { DEFAULT_MODEL_DIR },
    )

    fun modelFile(type: VoiceModelType, languageId: String): File? {
        val config = modelConfig(type, languageId) ?: return null
        return File(File(baseDir, languageId), config.fileName)
    }

    fun isModelAvailable(type: VoiceModelType, languageId: String): Boolean {
        val file = modelFile(type, languageId) ?: return false
        return file.exists() && file.length() > 0
    }

    fun hasAnyModels(type: VoiceModelType): Boolean {
        val models = when (type) {
            VoiceModelType.ASR -> voiceConfig.asr.models
            VoiceModelType.TTS -> voiceConfig.tts.models
        }
        return models.isNotEmpty()
    }

    suspend fun downloadModel(
        type: VoiceModelType,
        languageId: String,
        onProgress: (Int) -> Unit = {},
    ): Result<File> {
        val config = modelConfig(type, languageId)
            ?: return Result.failure(IllegalStateException("No model configured for $languageId ($type)"))

        if (config.url.isBlank()) {
            return Result.failure(IllegalStateException("Model URL missing for $languageId ($type)"))
        }

        return withContext(Dispatchers.IO) {
            val request = Request.Builder().url(config.url).build()
            val response = httpClient.newCall(request).execute()
            if (!response.isSuccessful) {
                response.close()
                return@withContext Result.failure(IllegalStateException("Download failed: ${response.code}"))
            }

            val body = response.body ?: run {
                response.close()
                return@withContext Result.failure(IllegalStateException("Empty response body"))
            }

            val targetDir = File(baseDir, languageId).apply { mkdirs() }
            val targetFile = File(targetDir, config.fileName)
            val tempFile = File(targetDir, "${config.fileName}.download")

            val totalBytes = body.contentLength().takeIf { it > 0L } ?: -1L
            val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
            var read: Int
            var written = 0L

            body.byteStream().use { input ->
                FileOutputStream(tempFile).use { output ->
                    while (true) {
                        read = input.read(buffer)
                        if (read == -1) break
                        output.write(buffer, 0, read)
                        written += read
                        if (totalBytes > 0) {
                            val progress = ((written * 100) / totalBytes).toInt()
                            onProgress(progress.coerceIn(0, 100))
                        }
                    }
                }
            }

            response.close()

            if (config.sha256.isNotBlank()) {
                val digest = sha256(tempFile)
                if (!digest.equals(config.sha256, ignoreCase = true)) {
                    tempFile.delete()
                    return@withContext Result.failure(IllegalStateException("Checksum mismatch"))
                }
            }

            tempFile.renameTo(targetFile)
            Result.success(targetFile)
        }
    }

    suspend fun downloadRequiredModels(
        languageId: String,
        onProgress: (Int) -> Unit = {},
    ): Result<Unit> {
        if (voiceConfig.asr.models.any { it.language == languageId }) {
            val result = downloadModel(VoiceModelType.ASR, languageId, onProgress)
            if (result.isFailure) return Result.failure(result.exceptionOrNull()!!)
        }
        if (voiceConfig.tts.models.any { it.language == languageId }) {
            val result = downloadModel(VoiceModelType.TTS, languageId, onProgress)
            if (result.isFailure) return Result.failure(result.exceptionOrNull()!!)
        }
        return Result.success(Unit)
    }

    fun areModelsReadyForLanguage(languageId: String): Boolean {
        val asrReady = voiceConfig.asr.models.none { it.language == languageId } ||
            isModelAvailable(VoiceModelType.ASR, languageId)
        val ttsReady = voiceConfig.tts.models.none { it.language == languageId } ||
            isModelAvailable(VoiceModelType.TTS, languageId)
        return asrReady && ttsReady
    }

    private fun modelConfig(type: VoiceModelType, languageId: String): VoiceModelConfig? {
        val models = when (type) {
            VoiceModelType.ASR -> voiceConfig.asr
            VoiceModelType.TTS -> voiceConfig.tts
        }
        return models.models.firstOrNull { it.language.equals(languageId, ignoreCase = true) }
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { stream ->
            val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
            var read = stream.read(buffer)
            while (read > 0) {
                digest.update(buffer, 0, read)
                read = stream.read(buffer)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    companion object {
        private const val DEFAULT_MODEL_DIR = "voice_models"
    }
}
