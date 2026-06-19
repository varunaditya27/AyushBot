package com.ayushbot.app.core.config

import android.content.Context
import com.ayushbot.app.voice.VoiceEngineType
import org.json.JSONArray
import org.json.JSONObject

// ═══════════════════════════════════════════════════════════════
// AppConfigLoader — loads config from assets/app_config.json
// Falls back to defaults when missing or malformed.
// ═══════════════════════════════════════════════════════════════

class AppConfigLoader(private val context: Context) {
    fun load(): AppConfig {
        val raw = runCatching {
            context.assets.open("app_config.json").bufferedReader().use { it.readText() }
        }.getOrNull()

        if (raw.isNullOrBlank()) {
            return AppConfig.default(context)
        }

        return runCatching { parse(JSONObject(raw)) }
            .getOrElse { AppConfig.default(context) }
    }

    private fun parse(root: JSONObject): AppConfig {
        val demoMode = root.optBoolean("demoMode", true)

        val mockJson = root.optJSONObject("mock") ?: JSONObject()
        val mock = MockConfig(
            useMockBackend = mockJson.optBoolean("useMockBackend", true),
            useMockSensors = mockJson.optBoolean("useMockSensors", true),
            useMockLlm = mockJson.optBoolean("useMockLlm", true),
        )

        val backendJson = root.optJSONObject("backend") ?: JSONObject()
        val backend = BackendConfig(
            baseUrl = backendJson.optString("baseUrl", "http://10.0.2.2:8000/"),
            mqttBrokerUrl = backendJson.optString("mqttBrokerUrl", "ssl://10.0.2.2:8883"),
            mqttClientId = backendJson.optString("mqttClientId", "ayushbot-android"),
            mqttUsername = backendJson.optString("mqttUsername", ""),
            mqttPassword = backendJson.optString("mqttPassword", ""),
        )

        val llmJson = root.optJSONObject("llm") ?: JSONObject()
        val llm = LlmConfig(
            modelPath = llmJson.optString(
                "modelPath",
                "/data/local/tmp/llm/gemma-3n-E4B-it-int4.litertlm",
            ),
            backend = llmJson.optString("backend", "CPU"),
            maxTokens = llmJson.optInt("maxTokens", 1024),
            topK = llmJson.optInt("topK", 40),
            topP = llmJson.optDouble("topP", 0.95),
            temperature = llmJson.optDouble("temperature", 0.8),
            systemPrompt = llmJson.optString(
                "systemPrompt",
                "You are AyushBot, an offline-first clinical decision support assistant for ASHA workers.",
            ),
            cacheDir = llmJson.optString("cacheDir", context.cacheDir.absolutePath),
            enableVision = llmJson.optBoolean("enableVision", false),
            enableAudio = llmJson.optBoolean("enableAudio", false),
        )

        val voiceJson = root.optJSONObject("voice") ?: JSONObject()
        val languages = parseLanguages(voiceJson.optJSONArray("languages"))
        val voice = VoiceConfig(
            enabled = voiceJson.optBoolean("enabled", true),
            offlineOnly = voiceJson.optBoolean("offlineOnly", true),
            primaryEngine = parseEngine(voiceJson.optString("primaryEngine", "INDIC")),
            fallbackEngine = parseEngine(voiceJson.optString("fallbackEngine", "ANDROID")),
            defaultLanguage = voiceJson.optString("defaultLanguage", "en"),
            sampleRateHz = voiceJson.optInt("sampleRateHz", 16000),
            modelBaseDir = voiceJson.optString("modelBaseDir", "voice_models"),
            languages = if (languages.isNotEmpty()) languages else defaultLanguages(),
            asr = parseAsrConfig(voiceJson.optJSONObject("asr")),
            tts = parseTtsConfig(voiceJson.optJSONObject("tts")),
        )

        return AppConfig(
            demoMode = demoMode,
            mock = mock,
            backend = backend,
            llm = llm,
            voice = voice,
        )
    }

    private fun parseEngine(raw: String): VoiceEngineType {
        return runCatching { VoiceEngineType.valueOf(raw.uppercase()) }
            .getOrElse { VoiceEngineType.ANDROID }
    }

    private fun parseLanguages(array: JSONArray?): List<VoiceLanguage> {
        if (array == null) return emptyList()
        val languages = mutableListOf<VoiceLanguage>()
        for (i in 0 until array.length()) {
            val item = array.optJSONObject(i) ?: continue
            languages += VoiceLanguage(
                id = item.optString("id", ""),
                label = item.optString("label", item.optString("id", "")),
                bcp47 = item.optString("bcp47", ""),
            )
        }
        return languages.filter { it.id.isNotBlank() && it.bcp47.isNotBlank() }
    }

    private fun parseAsrConfig(obj: JSONObject?): AsrConfig {
        val asr = obj ?: JSONObject()
        return AsrConfig(
            decoder = asr.optString("decoder", "ctc"),
            models = parseModels(asr.optJSONArray("models")),
        )
    }

    private fun parseTtsConfig(obj: JSONObject?): TtsConfig {
        val tts = obj ?: JSONObject()
        return TtsConfig(
            models = parseModels(tts.optJSONArray("models")),
        )
    }

    private fun parseModels(array: JSONArray?): List<VoiceModelConfig> {
        if (array == null) return emptyList()
        val models = mutableListOf<VoiceModelConfig>()
        for (i in 0 until array.length()) {
            val item = array.optJSONObject(i) ?: continue
            models += VoiceModelConfig(
                language = item.optString("language", ""),
                fileName = item.optString("fileName", ""),
                url = item.optString("url", ""),
                sha256 = item.optString("sha256", ""),
            )
        }
        return models.filter { it.language.isNotBlank() && it.fileName.isNotBlank() }
    }

    private fun defaultLanguages(): List<VoiceLanguage> {
        return listOf(
            VoiceLanguage(id = "en", label = "English", bcp47 = "en-US"),
            VoiceLanguage(id = "hi", label = "Hindi", bcp47 = "hi-IN"),
            VoiceLanguage(id = "kn", label = "Kannada", bcp47 = "kn-IN"),
            VoiceLanguage(id = "te", label = "Telugu", bcp47 = "te-IN"),
        )
    }
}
