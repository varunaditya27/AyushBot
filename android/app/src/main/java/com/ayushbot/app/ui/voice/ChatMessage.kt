package com.ayushbot.app.ui.voice

data class ChatMessage(
    val id: String,
    val text: String,
    val isUser: Boolean,
    val citation: String? = null,
)
