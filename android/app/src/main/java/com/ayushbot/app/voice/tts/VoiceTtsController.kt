package com.ayushbot.app.voice.tts

interface TtsListener {
    fun onStart(utteranceId: String) {}
    fun onDone(utteranceId: String)
    fun onError(utteranceId: String, message: String)
}

interface VoiceTtsController {
    suspend fun speak(
        text: String,
        languageId: String,
        utteranceId: String,
        listener: TtsListener,
        queueAdd: Boolean = false
    ): Boolean
    fun stop()
    fun isAvailable(languageId: String): Boolean
    fun shutdown()
}
