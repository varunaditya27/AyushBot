package com.ayushbot.app.ui.screens

sealed interface ScreenUiState<out T> {
    data object Loading : ScreenUiState<Nothing>
    data class Success<T>(val data: T) : ScreenUiState<T>
    data object Empty : ScreenUiState<Nothing>
    data class Error(val message: String, val canRetry: Boolean = true) : ScreenUiState<Nothing>
    data class Offline<T>(val cachedData: T? = null, val message: String) : ScreenUiState<T>
}

enum class VoiceMicState {
    IDLE,
    LISTENING,
    PROCESSING,
    ERROR,
}

enum class SyncState {
    SYNCED,
    PENDING,
    FAILED,
}
