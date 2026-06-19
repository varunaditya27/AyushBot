package com.ayushbot.app.voice.tts

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AndroidTtsController(
    private val context: Context,
) : VoiceTtsController {
    private var tts: TextToSpeech? = null
    private var initDeferred: CompletableDeferred<Boolean>? = null
    private val listeners = ConcurrentHashMap<String, TtsListener>()

    override suspend fun speak(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
    ): Boolean {
        val ready = ensureInitialized()
        if (!ready) {
            listener.onError(utteranceId, "TTS initialization failed")
            return false
        }

        val locale = Locale.forLanguageTag(languageId)
        val availability = tts?.setLanguage(locale) ?: TextToSpeech.LANG_NOT_SUPPORTED
        if (availability == TextToSpeech.LANG_MISSING_DATA || availability == TextToSpeech.LANG_NOT_SUPPORTED) {
            listener.onError(utteranceId, "Language not supported")
            return false
        }

        listeners[utteranceId] = listener
        val params = Bundle()
        val result = tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, utteranceId)
            ?: TextToSpeech.ERROR
        return result == TextToSpeech.SUCCESS
    }

    override fun stop() {
        tts?.stop()
    }

    override fun isAvailable(languageId: String): Boolean {
        return true
    }

    override fun shutdown() {
        listeners.clear()
        tts?.shutdown()
        tts = null
    }

    private suspend fun ensureInitialized(): Boolean {
        if (tts != null && initDeferred?.isCompleted == true) {
            return initDeferred?.getCompleted() ?: false
        }

        val deferred = initDeferred ?: CompletableDeferred<Boolean>().also { initDeferred = it }
        if (!deferred.isCompleted) {
            withContext(Dispatchers.Main) {
                tts = TextToSpeech(context) { status ->
                    val success = status == TextToSpeech.SUCCESS
                    if (success) {
                        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                            override fun onStart(utteranceId: String) {
                                listeners[utteranceId]?.onStart(utteranceId)
                            }

                            override fun onDone(utteranceId: String) {
                                listeners.remove(utteranceId)?.onDone(utteranceId)
                            }

                            override fun onError(utteranceId: String) {
                                listeners.remove(utteranceId)
                                    ?.onError(utteranceId, "TTS synthesis error")
                            }
                        })
                    }
                    if (!deferred.isCompleted) {
                        deferred.complete(success)
                    }
                }
            }
        }
        return deferred.await()
    }
}
