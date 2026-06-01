package com.ayushbot.app.core.di

import android.content.Context
import com.ayushbot.app.core.config.AppConfig
import com.ayushbot.app.core.config.AppConfigLoader
import com.ayushbot.app.data.local.AyushBotDatabase
import com.ayushbot.app.data.repository.BackendCaseRepository
import com.ayushbot.app.data.repository.CaseRepository
import com.ayushbot.app.data.repository.MockCaseRepository
import com.ayushbot.app.data.remote.BackendApiFactory
import com.ayushbot.app.llm.LiteRtLmChatEngine
import com.ayushbot.app.llm.LlmChatEngine
import com.ayushbot.app.llm.MockLlmChatEngine

// ═══════════════════════════════════════════════════════════════
// AppContainer — lightweight DI container for the Android app.
// Centralizes config + shared dependencies (LLM engine, repositories).
// ═══════════════════════════════════════════════════════════════

class AppContainer(context: Context) {
    val appConfig: AppConfig = AppConfigLoader(context).load()
    val database: AyushBotDatabase = AyushBotDatabase.getInstance(context)

    val llmChatEngine: LlmChatEngine = if (appConfig.mock.useMockLlm) {
        MockLlmChatEngine(appConfig.llm)
    } else {
        LiteRtLmChatEngine(context, appConfig.llm)
    }

    val caseRepository: CaseRepository = if (appConfig.mock.useMockBackend) {
        MockCaseRepository()
    } else {
        BackendCaseRepository(
            api = BackendApiFactory.create(appConfig.backend.baseUrl),
        )
    }
}
