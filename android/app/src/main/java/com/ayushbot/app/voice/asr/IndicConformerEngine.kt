package com.ayushbot.app.voice.asr

import com.ayushbot.app.voice.model.VoiceModelManager
import com.ayushbot.app.voice.model.VoiceModelType

class IndicConformerEngine(
    private val modelManager: VoiceModelManager,
) {
    fun isInferenceSupported(): Boolean = false

    fun isModelAvailable(languageId: String): Boolean {
        return modelManager.isModelAvailable(VoiceModelType.ASR, languageId)
    }

    suspend fun transcribe(
        pcmSamples: ShortArray,
        sampleRate: Int,
        languageId: String,
    ): Result<String> {
        if (!isModelAvailable(languageId)) {
            return Result.failure(IllegalStateException("IndicConformer model missing for $languageId"))
        }

        // TODO: Integrate ONNX Runtime inference for IndicConformer here.
        // Expect 16kHz mono PCM; convert to float32, run feature extraction + model inference.
        return Result.failure(UnsupportedOperationException("IndicConformer on-device inference not wired yet"))
    }
}
