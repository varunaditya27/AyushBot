package com.ayushbot.app.ui.voice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.ayushbot.app.core.config.AppConfig
import com.ayushbot.app.llm.LlmChatEngine
import com.ayushbot.app.llm.LlmStatus
import com.ayushbot.app.ui.screens.VoiceMicState
import com.ayushbot.app.voice.VoiceEngineType
import com.ayushbot.app.voice.VoiceOrchestrator
import com.ayushbot.app.voice.asr.AsrListener
import com.ayushbot.app.voice.tts.TtsListener
import com.ayushbot.app.core.config.VoiceLanguage
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
    val voiceEngine: VoiceEngineType? = null,
    val voiceLanguageId: String = "en",
    val voiceLanguageTag: String = "en-US",
    val voiceModelsReady: Boolean = true,
    val isDownloadingModels: Boolean = false,
    val voiceDownloadProgress: Int = 0,
    val voiceErrorMessage: String? = null,
    val partialTranscript: String? = null,
    val isSpeaking: Boolean = false,
    val voiceLanguageLabel: String = "English",
    val canDownloadVoiceModels: Boolean = false,
    val voiceReadinessMessage: String = "Android speech fallback is available.",
)

class VoiceQueryViewModel(
    private val chatEngine: LlmChatEngine,
    private val appConfig: AppConfig,
    private val voiceOrchestrator: VoiceOrchestrator,
) : ViewModel() {
    private val _uiState = MutableStateFlow(VoiceQueryUiState())
    val uiState: StateFlow<VoiceQueryUiState> = _uiState.asStateFlow()
    private var pendingMicStart = false

    private val asrListener = object : AsrListener {
        override fun onPartial(text: String) {
            _uiState.update { it.copy(partialTranscript = text) }
        }

        override fun onFinal(text: String) {
            _uiState.update { it.copy(partialTranscript = null) }
            submitText(text)
        }

        override fun onError(message: String) {
            _uiState.update {
                it.copy(
                    micState = VoiceMicState.ERROR,
                    voiceErrorMessage = message,
                )
            }
        }
    }

    private val ttsListener = object : TtsListener {
        override fun onStart(utteranceId: String) {
            _uiState.update { it.copy(isSpeaking = true) }
        }

        override fun onDone(utteranceId: String) {
            _uiState.update { it.copy(isSpeaking = false) }
        }

        override fun onError(utteranceId: String, message: String) {
            _uiState.update { it.copy(isSpeaking = false, voiceErrorMessage = message) }
        }
    }

    init {
        initializeVoiceState()
        warmUpLlm()
    }

    fun toggleOffline() {
        _uiState.update { it.copy(isOffline = !it.isOffline) }
    }

    fun onMicTapped(hasMicPermission: Boolean) {
        val current = _uiState.value.micState
        when (current) {
            VoiceMicState.IDLE -> startListening(hasMicPermission)
            VoiceMicState.LISTENING -> stopListening()
            VoiceMicState.PROCESSING -> Unit
            VoiceMicState.ERROR -> startListening(hasMicPermission)
        }
    }

    fun onMicPermissionResult(granted: Boolean) {
        if (!pendingMicStart) return
        pendingMicStart = false
        if (granted) {
            startListening(hasMicPermission = true)
        } else {
            _uiState.update {
                it.copy(
                    micState = VoiceMicState.ERROR,
                    voiceErrorMessage = "Microphone permission denied",
                )
            }
        }
    }

    fun clearVoiceError() {
        _uiState.update { it.copy(voiceErrorMessage = null) }
    }

    fun stopSpeaking() {
        voiceOrchestrator.stopSpeaking()
        _uiState.update { it.copy(isSpeaking = false) }
    }

    fun downloadVoiceModels() {
        val languageId = _uiState.value.voiceLanguageId
        if (_uiState.value.isDownloadingModels || !_uiState.value.canDownloadVoiceModels) return
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isDownloadingModels = true,
                    voiceDownloadProgress = 0,
                    voiceErrorMessage = null,
                )
            }
            val result = voiceOrchestrator.downloadModels(languageId) { progress ->
                _uiState.update { it.copy(voiceDownloadProgress = progress) }
            }
            result.onSuccess {
                _uiState.update {
                    it.copy(
                        isDownloadingModels = false,
                        voiceModelsReady = true,
                        voiceDownloadProgress = 100,
                        voiceReadinessMessage = "Indic voice models are ready for ${it.voiceLanguageLabel}.",
                    )
                }
            }.onFailure { error ->
                _uiState.update {
                    it.copy(
                        isDownloadingModels = false,
                        voiceErrorMessage = error.message ?: "Voice model download failed",
                    )
                }
            }
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
                speakLatestAssistantMessage()
            }
        }
    }

    private fun startListening(hasMicPermission: Boolean) {
        if (!appConfig.voice.enabled) {
            _uiState.update { it.copy(voiceErrorMessage = "Voice input is disabled in config") }
            return
        }
        if (!hasMicPermission) {
            pendingMicStart = true
            return
        }

        val languageId = _uiState.value.voiceLanguageId
        val languageTag = _uiState.value.voiceLanguageTag
        voiceOrchestrator.stopSpeaking()
        _uiState.update { it.copy(isSpeaking = false, partialTranscript = null) }
        val engine = voiceOrchestrator.startListening(languageId, languageTag, asrListener)
        if (engine == null) {
            _uiState.update {
                it.copy(
                    micState = VoiceMicState.ERROR,
                    voiceErrorMessage = "No available speech engine",
                )
            }
        } else {
            _uiState.update {
                it.copy(
                    micState = VoiceMicState.LISTENING,
                    voiceEngine = engine,
                    voiceErrorMessage = null,
                )
            }
        }
    }

    private fun stopListening() {
        _uiState.update { it.copy(micState = VoiceMicState.PROCESSING) }
        voiceOrchestrator.stopListening()
    }

    private fun initializeVoiceState() {
        val language = resolveDefaultLanguage()
        val modelsReady = voiceOrchestrator.areModelsReady(language.id)
        val canDownload = appConfig.voice.asr.models.any {
            it.language.equals(language.id, ignoreCase = true) && it.url.isNotBlank()
        } || appConfig.voice.tts.models.any {
            it.language.equals(language.id, ignoreCase = true) && it.url.isNotBlank()
        }
        val readinessMessage = when {
            language.id == "en" -> "English uses Android speech fallback in this demo."
            modelsReady -> "Indic voice models are present for ${language.label}; Android fallback remains available."
            canDownload -> "Indic voice models can be downloaded for ${language.label}."
            else -> "Indic model URLs are not configured yet; Android speech fallback will be used when available."
        }
        _uiState.update {
            it.copy(
                voiceLanguageId = language.id,
                voiceLanguageTag = language.bcp47,
                voiceModelsReady = modelsReady,
                voiceLanguageLabel = language.label,
                canDownloadVoiceModels = canDownload,
                voiceReadinessMessage = readinessMessage,
            )
        }
    }

    private fun resolveDefaultLanguage(): VoiceLanguage {
        val configured = appConfig.voice.defaultLanguage
        val languages = appConfig.voice.languages
        return languages.firstOrNull { it.id == configured }
            ?: languages.firstOrNull()
            ?: VoiceLanguage(id = "en", label = "English", bcp47 = "en-US")
    }

    private fun speakLatestAssistantMessage() {
        val lastAssistant = _uiState.value.messages.lastOrNull { !it.isUser } ?: return
        if (lastAssistant.text.isBlank()) return
        val languageId = _uiState.value.voiceLanguageId
        val languageTag = _uiState.value.voiceLanguageTag
        viewModelScope.launch {
            voiceOrchestrator.speak(
                text = lastAssistant.text,
                languageId = languageId,
                utteranceId = lastAssistant.id,
                listener = ttsListener,
                languageTag = languageTag,
            )
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
        voiceOrchestrator.shutdown()
        super.onCleared()
    }
}

class VoiceQueryViewModelFactory(
    private val chatEngine: LlmChatEngine,
    private val appConfig: AppConfig,
    private val voiceOrchestrator: VoiceOrchestrator,
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(VoiceQueryViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return VoiceQueryViewModel(chatEngine, appConfig, voiceOrchestrator) as T
        }
        error("Unknown ViewModel class")
    }
}
