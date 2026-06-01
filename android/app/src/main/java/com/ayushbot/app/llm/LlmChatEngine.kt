package com.ayushbot.app.llm

import kotlinx.coroutines.flow.Flow
import java.io.Closeable

// ═══════════════════════════════════════════════════════════════
// LlmChatEngine — abstraction over on-device LLM chat engines.
// ═══════════════════════════════════════════════════════════════

interface LlmChatEngine : Closeable {
    val modelPath: String

    fun modelExists(): Boolean

    suspend fun initialize()

    fun isInitialized(): Boolean

    fun streamReply(prompt: String): Flow<String>
}

sealed class LlmStatus {
    data object Idle : LlmStatus()
    data object Loading : LlmStatus()
    data object Ready : LlmStatus()
    data class MissingModel(val path: String) : LlmStatus()
    data class Error(val message: String) : LlmStatus()
}
