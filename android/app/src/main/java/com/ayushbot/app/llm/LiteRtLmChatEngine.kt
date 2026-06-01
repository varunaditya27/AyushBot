package com.ayushbot.app.llm

import android.content.Context
import com.ayushbot.app.core.config.LlmConfig
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.Conversation
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import com.google.ai.edge.litertlm.LogSeverity
import com.google.ai.edge.litertlm.SamplerConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.io.File

class LiteRtLmChatEngine(
    private val context: Context,
    private val config: LlmConfig,
) : LlmChatEngine {
    private val lock = Mutex()
    private var engine: Engine? = null
    private var conversation: Conversation? = null

    override val modelPath: String
        get() = config.modelPath

    override fun modelExists(): Boolean = File(config.modelPath).exists()

    override fun isInitialized(): Boolean = engine?.isInitialized() == true

    override suspend fun initialize() {
        if (isInitialized()) return

        withContext(Dispatchers.IO) {
            lock.withLock {
                if (isInitialized()) return@withLock
                Engine.setNativeMinLogSeverity(LogSeverity.ERROR)

                val cacheDir = config.cacheDir.ifBlank { context.cacheDir.absolutePath }
                val backend = config.backend.toBackend(context)
                val visionBackend = if (config.enableVision) backend else null
                val audioBackend = if (config.enableAudio) backend else null

                val engineConfig = EngineConfig(
                    modelPath = config.modelPath,
                    backend = backend,
                    visionBackend = visionBackend,
                    audioBackend = audioBackend,
                    maxNumTokens = config.maxTokens.takeIf { it > 0 },
                    cacheDir = cacheDir,
                )

                engine = Engine(engineConfig).also { it.initialize() }
            }
        }
    }

    override fun streamReply(prompt: String): Flow<String> = flow {
        initialize()
        val conversationInstance = getOrCreateConversation()
        conversationInstance.sendMessageAsync(prompt).collect { message ->
            emit(message.toString())
        }
    }

    override fun close() {
        conversation?.close()
        conversation = null
        engine?.close()
        engine = null
    }

    private fun getOrCreateConversation(): Conversation {
        val existing = conversation
        if (existing != null && existing.isAlive) return existing

        val samplerConfig = SamplerConfig(
            topK = config.topK,
            topP = config.topP,
            temperature = config.temperature,
        )

        val conversationConfig = ConversationConfig(
            systemInstruction = if (config.systemPrompt.isBlank()) {
                null
            } else {
                Contents.of(config.systemPrompt)
            },
            samplerConfig = samplerConfig,
        )

        return requireNotNull(engine) { "LLM engine not initialized." }
            .createConversation(conversationConfig)
            .also { conversation = it }
    }

    private fun String.toBackend(context: Context): Backend {
        return when (uppercase()) {
            "GPU" -> Backend.GPU()
            "NPU" -> Backend.NPU(context.applicationInfo.nativeLibraryDir)
            else -> Backend.CPU()
        }
    }
}
