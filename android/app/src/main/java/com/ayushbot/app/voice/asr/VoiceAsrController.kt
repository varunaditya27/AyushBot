package com.ayushbot.app.voice.asr

interface AsrListener {
    fun onPartial(text: String) {}
    fun onFinal(text: String)
    fun onError(message: String)
}

interface VoiceAsrController {
    fun startListening(languageId: String, listener: AsrListener): Boolean
    fun stopListening()
    fun cancel()
    fun isAvailable(languageId: String): Boolean
    fun shutdown()
}
