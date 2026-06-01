package com.ayushbot.app.ui.voice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.ayushbot.app.core.config.AppConfig
import com.ayushbot.app.llm.LlmChatEngine
import com.ayushbot.app.llm.LlmStatus
import com.ayushbot.app.ui.screens.VoiceMicState
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

private val initialConversation = listOf(
    ChatMessage(
        id = UUID.randomUUID().toString(),
        text = "What is the correct dose of ORS for a 2-year-old with moderate dehydration?",
        isUser = true,
    ),
    ChatMessage(
        id = UUID.randomUUID().toString(),
        text = "For a 2-year-old child (~12 kg) with moderate dehydration:\n\n" +
            "• Give 75 mL/kg of ORS solution over 4 hours\n" +
            "• That's approximately 900 mL over 4 hours\n" +
            "• Give frequent small sips using a cup\n" +
            "• If vomiting occurs, wait 10 minutes then continue slowly.",
        isUser = false,
        citation = "IMCI Chart Booklet, Sect. 5, p. 78",
    ),
)

data class VoiceQueryUiState(
    val messages: List<ChatMessage> = initialConversation,
    val micState: VoiceMicState = VoiceMicState.IDLE,
    val isOffline: Boolean = false,
    val isProcessing: Boolean = false,
    val llmStatus: LlmStatus = LlmStatus.Idle,
    val errorMessage: String? = null,
)

class VoiceQueryViewModel(
    private val chatEngine: LlmChatEngine,
    private val appConfig: AppConfig,
) : ViewModel() {
    private val _uiState = MutableStateFlow(VoiceQueryUiState())
    val uiState: StateFlow<VoiceQueryUiState> = _uiState.asStateFlow()

    init {
        warmUpLlm()
    }

    fun toggleOffline() {
        _uiState.update { it.copy(isOffline = !it.isOffline) }
    }

    fun onMicTapped() {
        val current = _uiState.value.micState
        when (current) {
            VoiceMicState.IDLE -> _uiState.update { it.copy(micState = VoiceMicState.LISTENING) }
            VoiceMicState.LISTENING -> simulateVoiceCapture()
            VoiceMicState.PROCESSING -> Unit
            VoiceMicState.ERROR -> _uiState.update { it.copy(micState = VoiceMicState.IDLE) }
        }
    }

    fun retryLlm() {
        warmUpLlm()
    }

    fun submitText(prompt: String) {
        if (prompt.isBlank() || _uiState.value.isProcessing) return

        if (!chatEngine.modelExists()) {
            _uiState.update {
                it.copy(llmStatus = LlmStatus.MissingModel(chatEngine.modelPath))
            }
            return
        }

        val userMessage = ChatMessage(
            id = UUID.randomUUID().toString(),
            text = prompt,
            isUser = true,
        )

        val assistantId = UUID.randomUUID().toString()
        val assistantMessage = ChatMessage(
            id = assistantId,
            text = "",
            isUser = false,
        )

        _uiState.update {
            it.copy(
                messages = it.messages + userMessage + assistantMessage,
                isProcessing = true,
                micState = VoiceMicState.PROCESSING,
                errorMessage = null,
            )
        }

        viewModelScope.launch {
            try {
                _uiState.update { it.copy(llmStatus = LlmStatus.Loading) }
                chatEngine.initialize()
                _uiState.update { it.copy(llmStatus = LlmStatus.Ready) }

                chatEngine.streamReply(prompt).collect { chunk ->
                    _uiState.update { state ->
                        state.copy(messages = state.messages.map { message ->
                            if (message.id == assistantId) {
                                message.copy(text = message.text + chunk)
                            } else {
                                message
                            }
                        })
                    }
                }
            } catch (throwable: Throwable) {
                _uiState.update {
                    it.copy(
                        llmStatus = LlmStatus.Error(throwable.message ?: "LLM error"),
                        errorMessage = "LLM error: ${throwable.message ?: "Unknown"}",
                    )
                }
            } finally {
                _uiState.update { it.copy(isProcessing = false, micState = VoiceMicState.IDLE) }
            }
        }
    }

    private fun simulateVoiceCapture() {
        _uiState.update { it.copy(micState = VoiceMicState.PROCESSING) }
        viewModelScope.launch {
            delay(1200)
            val hint = ChatMessage(
                id = UUID.randomUUID().toString(),
                text = "Voice capture is coming soon. For now, type your question for live on-device answers.",
                isUser = false,
                citation = "Voice module in progress",
            )
            _uiState.update {
                it.copy(
                    messages = it.messages + hint,
                    micState = VoiceMicState.IDLE,
                )
            }
        }
    }

    private fun warmUpLlm() {
        if (appConfig.mock.useMockLlm) {
            _uiState.update { it.copy(llmStatus = LlmStatus.Ready) }
            return
        }

        if (!chatEngine.modelExists()) {
            _uiState.update { it.copy(llmStatus = LlmStatus.MissingModel(chatEngine.modelPath)) }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(llmStatus = LlmStatus.Loading) }
            runCatching { chatEngine.initialize() }
                .onSuccess {
                    _uiState.update { it.copy(llmStatus = LlmStatus.Ready) }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(
                            llmStatus = LlmStatus.Error(error.message ?: "LLM initialization failed"),
                            errorMessage = "LLM init failed: ${error.message ?: "Unknown"}",
                        )
                    }
                }
        }
    }

    override fun onCleared() {
        chatEngine.close()
        super.onCleared()
    }
}

class VoiceQueryViewModelFactory(
    private val chatEngine: LlmChatEngine,
    private val appConfig: AppConfig,
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(VoiceQueryViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return VoiceQueryViewModel(chatEngine, appConfig) as T
        }
        error("Unknown ViewModel class")
    }
}
