package com.ayushbot.app.voice

import com.ayushbot.app.core.config.VoiceConfig
import com.ayushbot.app.voice.asr.AsrListener
import com.ayushbot.app.voice.asr.VoiceAsrController
import com.ayushbot.app.voice.model.VoiceModelManager
import com.ayushbot.app.voice.tts.TtsListener
import com.ayushbot.app.voice.tts.VoiceTtsController

class VoiceOrchestrator(
    private val config: VoiceConfig,
    private val modelManager: VoiceModelManager,
    private val indicAsr: VoiceAsrController,
    private val androidAsr: VoiceAsrController,
    private val indicTts: VoiceTtsController,
    private val androidTts: VoiceTtsController,
) {
    private var activeAsr: VoiceAsrController? = null
    private var activeTts: VoiceTtsController? = null

    fun startListening(languageId: String, languageTag: String? = null, listener: AsrListener): VoiceEngineType? {
        if (!config.enabled) return null
        val selected = resolveAsr(languageId) ?: return null
        val started = startAsrSelection(selected, languageId, languageTag, listener)
        if (started != null) return started

        val fallback = fallbackAsr(languageId, failedType = selected.type) ?: return null
        return startAsrSelection(fallback, languageId, languageTag, listener)
    }

    fun stopListening() {
        activeAsr?.stopListening()
    }

    fun cancelListening() {
        activeAsr?.cancel()
    }

    suspend fun speak(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
        languageTag: String? = null,
    ): VoiceEngineType? {
        if (!config.enabled) return null
        val selected = resolveTts(languageId) ?: return null
        activeTts = selected.controller
        val controllerLanguage = if (selected.type == VoiceEngineType.ANDROID) {
            languageTag ?: languageId
        } else {
            languageId
        }
        val success = selected.controller.speak(text, controllerLanguage, utteranceId, listener)
        return if (success) selected.type else fallbackTts(
            text = text,
            languageId = languageId,
            utteranceId = utteranceId,
            listener = listener,
            failedType = selected.type,
            languageTag = languageTag,
        )
    }

    fun stopSpeaking() {
        activeTts?.stop()
    }

    fun shutdown() {
        indicAsr.shutdown()
        androidAsr.shutdown()
        indicTts.shutdown()
        androidTts.shutdown()
    }

    fun areModelsReady(languageId: String): Boolean {
        return modelManager.areModelsReadyForLanguage(languageId)
    }

    suspend fun downloadModels(languageId: String, onProgress: (Int) -> Unit = {}): Result<Unit> {
        return modelManager.downloadRequiredModels(languageId, onProgress)
    }

    private suspend fun fallbackTts(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
        failedType: VoiceEngineType,
        languageTag: String? = null,
    ): VoiceEngineType? {
        val fallbackType = config.fallbackEngine
        if (fallbackType == failedType) return null
        val fallbackController = when (fallbackType) {
            VoiceEngineType.INDIC -> indicTts
            VoiceEngineType.ANDROID -> androidTts
        }
        if (!fallbackController.isAvailable(languageId)) return null
        activeTts = fallbackController
        val controllerLanguage = if (fallbackType == VoiceEngineType.ANDROID) {
            languageTag ?: languageId
        } else {
            languageId
        }
        val success = fallbackController.speak(text, controllerLanguage, utteranceId, listener)
        return if (success) fallbackType else null
    }

    private data class AsrSelection(val type: VoiceEngineType, val controller: VoiceAsrController)
    private data class TtsSelection(val type: VoiceEngineType, val controller: VoiceTtsController)

    private fun startAsrSelection(
        selection: AsrSelection,
        languageId: String,
        languageTag: String?,
        listener: AsrListener,
    ): VoiceEngineType? {
        val controllerLanguage = if (selection.type == VoiceEngineType.ANDROID) {
            languageTag ?: languageId
        } else {
            languageId
        }
        return if (selection.controller.startListening(controllerLanguage, listener)) {
            activeAsr = selection.controller
            selection.type
        } else {
            null
        }
    }

    private fun resolveAsr(languageId: String): AsrSelection? {
        val primary = when (config.primaryEngine) {
            VoiceEngineType.INDIC -> AsrSelection(VoiceEngineType.INDIC, indicAsr)
            VoiceEngineType.ANDROID -> AsrSelection(VoiceEngineType.ANDROID, androidAsr)
        }
        if (primary.controller.isAvailable(languageId)) return primary

        val fallback = when (config.fallbackEngine) {
            VoiceEngineType.INDIC -> AsrSelection(VoiceEngineType.INDIC, indicAsr)
            VoiceEngineType.ANDROID -> AsrSelection(VoiceEngineType.ANDROID, androidAsr)
        }
        return fallback.takeIf { it.controller.isAvailable(languageId) }
    }

    private fun fallbackAsr(languageId: String, failedType: VoiceEngineType): AsrSelection? {
        val fallbackType = config.fallbackEngine
        if (fallbackType == failedType) return null
        val fallback = when (fallbackType) {
            VoiceEngineType.INDIC -> AsrSelection(VoiceEngineType.INDIC, indicAsr)
            VoiceEngineType.ANDROID -> AsrSelection(VoiceEngineType.ANDROID, androidAsr)
        }
        return fallback.takeIf { it.controller.isAvailable(languageId) }
    }

    private fun resolveTts(languageId: String): TtsSelection? {
        val primary = when (config.primaryEngine) {
            VoiceEngineType.INDIC -> TtsSelection(VoiceEngineType.INDIC, indicTts)
            VoiceEngineType.ANDROID -> TtsSelection(VoiceEngineType.ANDROID, androidTts)
        }
        if (primary.controller.isAvailable(languageId)) return primary

        val fallback = when (config.fallbackEngine) {
            VoiceEngineType.INDIC -> TtsSelection(VoiceEngineType.INDIC, indicTts)
            VoiceEngineType.ANDROID -> TtsSelection(VoiceEngineType.ANDROID, androidTts)
        }
        return fallback.takeIf { it.controller.isAvailable(languageId) }
    }
}
