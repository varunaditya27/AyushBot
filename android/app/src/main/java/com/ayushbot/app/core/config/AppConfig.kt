package com.ayushbot.app.core.config

import android.content.Context
import com.ayushbot.app.voice.VoiceEngineType

// ═══════════════════════════════════════════════════════════════
// AppConfig — runtime configuration loaded from assets/app_config.json
// Used to toggle demo/mock behavior and configure LLM/backend settings.
// ═══════════════════════════════════════════════════════════════

data class AppConfig(
    val demoMode: Boolean,
    val mock: MockConfig,
    val backend: BackendConfig,
    val llm: LlmConfig,
    val voice: VoiceConfig,
) {
    companion object {
        fun default(context: Context) = AppConfig(
            demoMode = true,
            mock = MockConfig(
                useMockBackend = true,
                useMockSensors = true,
                useMockLlm = true,
            ),
            backend = BackendConfig(
                baseUrl = "http://10.0.2.2:8000/",
                mqttBrokerUrl = "ssl://10.0.2.2:8883",
                mqttClientId = "ayushbot-android",
                mqttUsername = "",
                mqttPassword = "",
            ),
            llm = LlmConfig(
                modelPath = "/data/local/tmp/llm/gemma-3n-E4B-it-int4.litertlm",
                backend = "CPU",
                maxTokens = 1024,
                topK = 40,
                topP = 0.95,
                temperature = 0.8,
                systemPrompt = "You are AyushBot, an offline-first clinical decision support assistant for ASHA workers.",
                cacheDir = context.cacheDir.absolutePath,
                enableVision = false,
                enableAudio = false,
            ),
            voice = VoiceConfig(
                enabled = true,
                offlineOnly = true,
                primaryEngine = VoiceEngineType.ANDROID,
                fallbackEngine = VoiceEngineType.ANDROID,
                defaultLanguage = "en",
                sampleRateHz = 16000,
                modelBaseDir = "voice_models",
                languages = listOf(
                    VoiceLanguage(id = "en", label = "English", bcp47 = "en-US"),
                    VoiceLanguage(id = "hi", label = "Hindi", bcp47 = "hi-IN"),
                    VoiceLanguage(id = "kn", label = "Kannada", bcp47 = "kn-IN"),
                    VoiceLanguage(id = "te", label = "Telugu", bcp47 = "te-IN"),
                ),
                asr = AsrConfig(
                    decoder = "ctc",
                    models = emptyList(),
                ),
                tts = TtsConfig(
                    models = emptyList(),
                ),
            ),
        )
    }
}

data class MockConfig(
    val useMockBackend: Boolean,
    val useMockSensors: Boolean,
    val useMockLlm: Boolean,
)

data class BackendConfig(
    val baseUrl: String,
    val mqttBrokerUrl: String,
    val mqttClientId: String,
    val mqttUsername: String,
    val mqttPassword: String,
)

data class LlmConfig(
    val modelPath: String,
    val backend: String,
    val maxTokens: Int,
    val topK: Int,
    val topP: Double,
    val temperature: Double,
    val systemPrompt: String,
    val cacheDir: String,
    val enableVision: Boolean,
    val enableAudio: Boolean,
)

data class VoiceConfig(
    val enabled: Boolean,
    val offlineOnly: Boolean,
    val primaryEngine: VoiceEngineType,
    val fallbackEngine: VoiceEngineType,
    val defaultLanguage: String,
    val sampleRateHz: Int,
    val modelBaseDir: String,
    val languages: List<VoiceLanguage>,
    val asr: AsrConfig,
    val tts: TtsConfig,
)

data class VoiceLanguage(
    val id: String,
    val label: String,
    val bcp47: String,
)

data class VoiceModelConfig(
    val language: String,
    val fileName: String,
    val url: String,
    val sha256: String = "",
)

data class AsrConfig(
    val decoder: String,
    val models: List<VoiceModelConfig>,
)

data class TtsConfig(
    val models: List<VoiceModelConfig>,
)
