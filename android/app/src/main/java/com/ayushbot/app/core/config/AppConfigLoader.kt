package com.ayushbot.app.core.config

import android.content.Context
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

        return AppConfig(
            demoMode = demoMode,
            mock = mock,
            backend = backend,
            llm = llm,
        )
    }
}
