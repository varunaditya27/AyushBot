package com.ayushbot.app.voice.asr

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import java.util.Locale

class AndroidSpeechRecognizerController(
    private val context: Context,
    private val offlineOnly: Boolean,
) : VoiceAsrController {
    private var speechRecognizer: SpeechRecognizer? = null
    private var listener: AsrListener? = null
    private var isListening = false

    override fun startListening(languageId: String, listener: AsrListener): Boolean {
        if (!isAvailable(languageId)) return false
        if (speechRecognizer == null) {
            speechRecognizer = if (offlineOnly && SpeechRecognizer.isOnDeviceRecognitionAvailable(context)) {
                SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
            } else {
                SpeechRecognizer.createSpeechRecognizer(context)
            }
            speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) = Unit
                override fun onBeginningOfSpeech() = Unit
                override fun onRmsChanged(rmsdB: Float) = Unit
                override fun onBufferReceived(buffer: ByteArray?) = Unit
                override fun onEndOfSpeech() = Unit

                override fun onError(error: Int) {
                    isListening = false
                    this@AndroidSpeechRecognizerController.listener?.onError(errorMessage(error))
                }

                override fun onResults(results: Bundle?) {
                    isListening = false
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val text = matches?.firstOrNull().orEmpty()
                    if (text.isBlank()) {
                        this@AndroidSpeechRecognizerController.listener?.onError("No speech recognized")
                    } else {
                        this@AndroidSpeechRecognizerController.listener?.onFinal(text)
                    }
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val text = matches?.firstOrNull().orEmpty()
                    if (text.isNotBlank()) {
                        this@AndroidSpeechRecognizerController.listener?.onPartial(text)
                    }
                }

                override fun onEvent(eventType: Int, params: Bundle?) = Unit
            })
        }

        this.listener = listener
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageId)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, offlineOnly)
        }
        isListening = true
        speechRecognizer?.startListening(intent)
        return true
    }

    override fun stopListening() {
        if (!isListening) return
        speechRecognizer?.stopListening()
    }

    override fun cancel() {
        isListening = false
        speechRecognizer?.cancel()
    }

    override fun isAvailable(languageId: String): Boolean {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) return false
        if (offlineOnly && !SpeechRecognizer.isOnDeviceRecognitionAvailable(context)) return false
        return true
    }

    override fun shutdown() {
        isListening = false
        speechRecognizer?.destroy()
        speechRecognizer = null
    }

    private fun errorMessage(error: Int): String {
        return when (error) {
            SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
            SpeechRecognizer.ERROR_CLIENT -> "Client error"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission missing"
            SpeechRecognizer.ERROR_NETWORK -> "Network error"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
            SpeechRecognizer.ERROR_NO_MATCH -> "No speech recognized"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
            SpeechRecognizer.ERROR_SERVER -> "Server error"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input"
            SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED -> "Language not supported"
            SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "Language unavailable"
            else -> "Speech recognition error"
        }
    }
}
