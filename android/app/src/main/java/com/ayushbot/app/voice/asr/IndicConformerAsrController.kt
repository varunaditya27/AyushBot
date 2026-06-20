package com.ayushbot.app.voice.asr

import com.ayushbot.app.voice.audio.AudioRecorder
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class IndicConformerAsrController(
    private val audioRecorder: AudioRecorder,
    private val engine: IndicConformerEngine,
    private val scope: CoroutineScope,
    private val sampleRate: Int,
) : VoiceAsrController {
    private var listener: AsrListener? = null
    private var activeLanguageId: String = ""

    override fun startListening(languageId: String, listener: AsrListener): Boolean {
        if (!isAvailable(languageId)) return false
        this.listener = listener
        activeLanguageId = languageId
        return audioRecorder.start()
    }

    override fun stopListening() {
        if (!audioRecorder.isActive()) return
        val samples = audioRecorder.stop()
        val languageId = activeLanguageId
        scope.launch(Dispatchers.Default) {
            val result = engine.transcribe(samples, sampleRate, languageId)
            result.onSuccess { text ->
                if (text.isBlank()) {
                    listener?.onError("No speech recognized")
                } else {
                    listener?.onFinal(text)
                }
            }.onFailure { error ->
                listener?.onError(error.message ?: "ASR failed")
            }
        }
    }

    override fun cancel() {
        audioRecorder.cancel()
    }

    override fun isAvailable(languageId: String): Boolean {
        return engine.isInferenceSupported() && engine.isModelAvailable(languageId)
    }

    override fun shutdown() {
        audioRecorder.cancel()
    }
}
