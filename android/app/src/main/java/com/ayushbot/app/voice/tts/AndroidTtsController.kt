package com.ayushbot.app.voice.tts

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap

// ═══════════════════════════════════════════════════════════════
// AndroidTtsController — wraps the Android TextToSpeech engine.
//
// Key design decisions:
//  • TTS initialization is lazy but guarded by a CompletableDeferred
//    so concurrent callers share one initialization cycle.
//  • isAvailable() uses the TTS instance status if available,
//    or returns true optimistically (initialization will verify).
//  • speak() awaits initialization before enqueueing text.
//  • All listener callbacks are thread-safe via ConcurrentHashMap.
// ═══════════════════════════════════════════════════════════════

class AndroidTtsController(
    private val context: Context,
) : VoiceTtsController {
    private var tts: TextToSpeech? = null

    // Guarded by a single CompletableDeferred — all coroutines waiting on
    // speak() share one init cycle; no double-initialization possible.
    @Volatile private var initDeferred: CompletableDeferred<Boolean>? = null

    private val listeners = ConcurrentHashMap<String, TtsListener>()

    override suspend fun speak(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
        queueAdd: Boolean,
    ): Boolean {
        val ready = ensureInitialized()
        if (!ready) {
            listener.onError(utteranceId, "TTS initialization failed")
            return false
        }

        val locale = parseLocale(languageId)
        val availability = tts?.setLanguage(locale) ?: TextToSpeech.LANG_NOT_SUPPORTED
        if (availability == TextToSpeech.LANG_MISSING_DATA ||
            availability == TextToSpeech.LANG_NOT_SUPPORTED
        ) {
            // Try falling back to just the language without region (e.g. "en" from "en-US")
            val baseLocale = Locale(locale.language)
            val baseAvailability = tts?.setLanguage(baseLocale) ?: TextToSpeech.LANG_NOT_SUPPORTED
            if (baseAvailability == TextToSpeech.LANG_MISSING_DATA ||
                baseAvailability == TextToSpeech.LANG_NOT_SUPPORTED
            ) {
                listener.onError(utteranceId, "Language not supported: $languageId")
                return false
            }
        }

        listeners[utteranceId] = listener
        val params = Bundle()
        val queueMode = if (queueAdd) TextToSpeech.QUEUE_ADD else TextToSpeech.QUEUE_FLUSH
        val result = tts?.speak(text, queueMode, params, utteranceId)
            ?: TextToSpeech.ERROR
        if (result != TextToSpeech.SUCCESS) {
            listeners.remove(utteranceId)
            listener.onError(utteranceId, "TTS speak() failed")
            return false
        }
        return true
    }

    override fun stop() {
        tts?.stop()
    }

    override fun isAvailable(languageId: String): Boolean {
        val engine = tts ?: return true // Optimistically available; ensureInitialized() will verify
        val locale = parseLocale(languageId)
        val availability = engine.isLanguageAvailable(locale)
        if (availability != TextToSpeech.LANG_MISSING_DATA &&
            availability != TextToSpeech.LANG_NOT_SUPPORTED
        ) {
            return true
        }
        // Try base language
        val baseLocale = Locale(locale.language)
        val baseAvailability = engine.isLanguageAvailable(baseLocale)
        return baseAvailability != TextToSpeech.LANG_MISSING_DATA &&
            baseAvailability != TextToSpeech.LANG_NOT_SUPPORTED
    }

    override fun shutdown() {
        listeners.clear()
        tts?.shutdown()
        tts = null
        initDeferred = null
    }

    // ──────────────────────────────────────────────
    // Private helpers
    // ──────────────────────────────────────────────

    private suspend fun ensureInitialized(): Boolean {
        // Fast path: already initialized successfully
        val existing = initDeferred
        if (existing != null && existing.isCompleted) {
            return existing.await()
        }

        // Slow path: start initialization (only one coroutine does it; others wait)
        val deferred = synchronized(this) {
            initDeferred ?: CompletableDeferred<Boolean>().also { initDeferred = it }
        }

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

                            @Deprecated("Deprecated in Java")
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

    /**
     * Parses a BCP-47 tag (e.g. "en-US") or a simple language code (e.g. "en")
     * into a [Locale]. Falls back to [Locale.ENGLISH] if unparseable.
     */
    private fun parseLocale(languageId: String): Locale {
        return try {
            Locale.forLanguageTag(languageId).takeIf { it.language.isNotEmpty() }
                ?: Locale(languageId)
        } catch (_: Exception) {
            Locale.ENGLISH
        }
    }
}
