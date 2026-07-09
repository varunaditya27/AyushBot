package com.ayushbot.app.llm

import com.ayushbot.app.core.config.LlmConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class MockLlmChatEngine(private val config: LlmConfig) : LlmChatEngine {
    override val modelPath: String
        get() = config.modelPath

    override fun modelExists(): Boolean = true

    override suspend fun initialize() = Unit

    override fun isInitialized(): Boolean = true

    override fun streamReply(prompt: String): Flow<String> = flow {
        emit(
            "This is a mock response. Switch off useMockLlm in app_config.json to " +
                "use on-device Gemma 3n inference."
        )
    }

    override fun resetConversation() = Unit

    override fun close() = Unit
}
