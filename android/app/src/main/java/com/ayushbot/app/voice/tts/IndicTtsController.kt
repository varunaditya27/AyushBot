package com.ayushbot.app.voice.tts

import com.ayushbot.app.voice.model.VoiceModelManager
import com.ayushbot.app.voice.model.VoiceModelType

class IndicTtsController(
    private val modelManager: VoiceModelManager,
) : VoiceTtsController {
    private fun isInferenceSupported(): Boolean = false

    override suspend fun speak(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
        queueAdd: Boolean,
    ): Boolean {
        if (!isAvailable(languageId)) {
            listener.onError(utteranceId, "Indic-TTS model missing for $languageId")
            return false
        }

        // TODO: Integrate Indic-TTS (FastPitch + HiFi-GAN) inference here.
        listener.onError(utteranceId, "Indic-TTS on-device inference not wired yet")
        return false
    }

    override fun stop() {
        // TODO: Stop Indic-TTS playback when implemented.
    }

    override fun isAvailable(languageId: String): Boolean {
        return isInferenceSupported() && modelManager.isModelAvailable(VoiceModelType.TTS, languageId)
    }

    override fun shutdown() {
        // TODO: Release Indic-TTS resources when implemented.
    }
}
