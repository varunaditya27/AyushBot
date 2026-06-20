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
import com.ayushbot.app.voice.VoiceOrchestrator
import com.ayushbot.app.voice.asr.AndroidSpeechRecognizerController
import com.ayushbot.app.voice.asr.IndicConformerAsrController
import com.ayushbot.app.voice.asr.IndicConformerEngine
import com.ayushbot.app.voice.audio.AudioRecorder
import com.ayushbot.app.voice.model.VoiceModelManager
import com.ayushbot.app.voice.tts.AndroidTtsController
import com.ayushbot.app.voice.tts.IndicTtsController
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

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

    private val voiceScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private val voiceModelManager = VoiceModelManager(context, appConfig.voice)

    val voiceOrchestrator: VoiceOrchestrator = VoiceOrchestrator(
        config = appConfig.voice,
        modelManager = voiceModelManager,
        indicAsr = IndicConformerAsrController(
            audioRecorder = AudioRecorder(appConfig.voice.sampleRateHz),
            engine = IndicConformerEngine(voiceModelManager),
            scope = voiceScope,
            sampleRate = appConfig.voice.sampleRateHz,
        ),
        androidAsr = AndroidSpeechRecognizerController(
            context = context,
            offlineOnly = appConfig.voice.offlineOnly,
        ),
        indicTts = IndicTtsController(voiceModelManager),
        androidTts = AndroidTtsController(context),
    )
}
