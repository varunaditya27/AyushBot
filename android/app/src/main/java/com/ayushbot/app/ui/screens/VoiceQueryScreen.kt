package com.ayushbot.app.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material.icons.rounded.Translate
import androidx.compose.material3.AssistChip
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ayushbot.app.core.di.LocalAppContainer
import com.ayushbot.app.llm.LlmStatus
import com.ayushbot.app.ui.components.ErrorStateCard
import com.ayushbot.app.ui.components.OfflineStateCard
import com.ayushbot.app.ui.components.PlaybackStateCard
import com.ayushbot.app.ui.theme.AyushBotDesignSystem
import com.ayushbot.app.ui.voice.ChatMessage
import com.ayushbot.app.ui.voice.VoiceQueryViewModel
import com.ayushbot.app.ui.voice.VoiceQueryViewModelFactory

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceQueryScreen(
    onBack: () -> Unit,
) {
    val spacing = AyushBotDesignSystem.spacing
    val appContainer = LocalAppContainer.current
    val context = LocalContext.current
    val viewModel: VoiceQueryViewModel = viewModel(
        factory = VoiceQueryViewModelFactory(
            chatEngine = appContainer.llmChatEngine,
            appConfig = appContainer.appConfig,
            voiceOrchestrator = appContainer.voiceOrchestrator,
            voiceTurnDao = appContainer.database.voiceTurnDao(),
            context = context.applicationContext,
        ),
    )
    val uiState by viewModel.uiState.collectAsState()
    val micPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = viewModel::onMicPermissionResult,
    )
    var inputText by remember { mutableStateOf("") }
    val micState = uiState.micState
    val messages = uiState.messages
    val isOffline = uiState.isOffline
    fun handleMicTap() {
        val hasPermission = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        viewModel.onMicTapped(hasPermission)
        if (!hasPermission) {
            micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Voice Ask AyushBot", style = MaterialTheme.typography.titleMedium)
                        Text(
                            "Ask any clinical question",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        bottomBar = {
            Surface(
                color = MaterialTheme.colorScheme.surface,
                tonalElevation = 2.dp,
                modifier = Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .imePadding(),
            ) {
                Column {
                    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(spacing.md),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        val pulseTransition = rememberInfiniteTransition(label = "voice_mic_pulse")
                        val pulse by pulseTransition.animateFloat(
                            initialValue = 1f,
                            targetValue = 1.08f,
                            animationSpec = infiniteRepeatable(
                                animation = tween(650, easing = LinearEasing),
                                repeatMode = RepeatMode.Reverse,
                            ),
                            label = "mic_scale",
                        )

                        FloatingActionButton(
                            onClick = ::handleMicTap,
                            modifier = Modifier
                                .size(48.dp)
                                .graphicsLayer {
                                    scaleX = if (micState == VoiceMicState.LISTENING) pulse else 1f
                                    scaleY = if (micState == VoiceMicState.LISTENING) pulse else 1f
                                },
                            containerColor = if (micState == VoiceMicState.LISTENING) {
                                MaterialTheme.colorScheme.primary
                            } else {
                                MaterialTheme.colorScheme.primaryContainer
                            },
                            contentColor = if (micState == VoiceMicState.LISTENING) {
                                MaterialTheme.colorScheme.onPrimary
                            } else {
                                MaterialTheme.colorScheme.primary
                            },
                        ) {
                            Icon(Icons.Rounded.Mic, "Voice input", modifier = Modifier.size(24.dp))
                        }

                        OutlinedTextField(
                            value = inputText,
                            onValueChange = {
                                inputText = it
                                if (uiState.voiceErrorMessage != null) {
                                    viewModel.clearVoiceError()
                                }
                            },
                            placeholder = {
                                Text(
                                    when (micState) {
                                        VoiceMicState.IDLE -> "Type or speak your question..."
                                        VoiceMicState.LISTENING -> "Listening..."
                                        VoiceMicState.PROCESSING -> "Processing..."
                                        VoiceMicState.ERROR -> "Voice input failed. Try again."
                                    }
                                )
                            },
                            modifier = Modifier.weight(1f),
                            shape = MaterialTheme.shapes.extraLarge,
                            singleLine = true,
                            trailingIcon = {
                                if (inputText.isNotBlank()) {
                                    IconButton(onClick = {
                                        viewModel.submitText(inputText)
                                        inputText = ""
                                    }) {
                                        Icon(Icons.AutoMirrored.Rounded.Send, "Send", tint = MaterialTheme.colorScheme.primary)
                                    }
                                }
                            },
                        )
                    }
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            // Dedicated status indicator row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(horizontal = spacing.lg, vertical = spacing.xs),
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                AssistChip(
                    onClick = viewModel::toggleLanguage,
                    label = { Text(uiState.voiceLanguageLabel) },
                    leadingIcon = {
                        Icon(Icons.Rounded.Translate, contentDescription = "Toggle Language", modifier = Modifier.size(16.dp))
                    },
                )
                AssistChip(
                    onClick = viewModel::toggleOffline,
                    label = {
                        Text(if (isOffline) "Offline" else "Online")
                    },
                    leadingIcon = {
                        Icon(Icons.Rounded.Sync, contentDescription = null, modifier = Modifier.size(16.dp))
                    },
                )
                AssistChip(
                    onClick = { },
                    label = { Text(llmStatusLabel(uiState.llmStatus)) },
                    leadingIcon = {
                        Icon(Icons.Rounded.AutoAwesome, contentDescription = null, modifier = Modifier.size(16.dp))
                    },
                )
                AssistChip(
                    onClick = { },
                    label = { Text(voiceStatusLabel(uiState.voiceEngine, uiState.isSpeaking)) },
                    leadingIcon = {
                        Icon(Icons.Rounded.Mic, contentDescription = null, modifier = Modifier.size(16.dp))
                    },
                )
            }

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(horizontal = spacing.lg, vertical = spacing.md),
                verticalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
            if (isOffline) {
                item {
                    OfflineStateCard(
                        title = "Local mode active",
                        subtitle = "Cloud-enhanced responses are unavailable. Clinical protocol-safe responses remain available.",
                    )
                }
            }

            when (val status = uiState.llmStatus) {
                is LlmStatus.MissingModel -> {
                    item {
                        ErrorStateCard(
                            title = "Model file not found",
                            subtitle = "Expected model at ${status.path}. Update app_config.json or push the .litertlm file to the device.",
                            onRetry = viewModel::retryLlm,
                        )
                    }
                }
                is LlmStatus.Error -> {
                    item {
                        ErrorStateCard(
                            title = "LLM error",
                            subtitle = status.message,
                            onRetry = viewModel::retryLlm,
                        )
                    }
                }
                else -> Unit
            }

            item {
                VoiceReadinessCard(
                    languageLabel = uiState.voiceLanguageLabel,
                    message = uiState.voiceReadinessMessage,
                    modelsReady = uiState.voiceModelsReady,
                    canDownload = uiState.canDownloadVoiceModels,
                    isDownloading = uiState.isDownloadingModels,
                    downloadProgress = uiState.voiceDownloadProgress,
                    onDownload = viewModel::downloadVoiceModels,
                )
            }

            if (uiState.partialTranscript != null) {
                item {
                    Surface(
                        shape = MaterialTheme.shapes.large,
                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.55f),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(spacing.md)) {
                            Text(
                                text = "Heard so far",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Medium,
                            )
                            Spacer(Modifier.height(spacing.xs))
                            Text(
                                text = uiState.partialTranscript.orEmpty(),
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                        }
                    }
                }
            }

            if (micState == VoiceMicState.ERROR) {
                item {
                    ErrorStateCard(
                        title = "Voice processing failed",
                        subtitle = uiState.voiceErrorMessage ?: "Please retry voice input or type your question.",
                        onRetry = ::handleMicTap,
                    )
                }
            }

            if (uiState.isSpeaking) {
                item {
                    PlaybackStateCard(
                        title = "Reading response aloud",
                        subtitle = "Tap stop if the playback is no longer needed.",
                        actionLabel = "Stop",
                        onStop = viewModel::stopSpeaking,
                    )
                }
            }

            items(messages) { message ->
                ChatBubble(message = message)
            }

            if (uiState.isProcessing) {
                item {
                    ChatBubble(
                        message = ChatMessage(
                            id = "thinking",
                            text = "Thinking...",
                            isUser = false,
                        )
                    )
                }
            }
        }
    }
}
}

private fun llmStatusLabel(status: LlmStatus): String {
    return when (status) {
        LlmStatus.Idle -> "LLM: idle"
        LlmStatus.Loading -> "LLM: loading"
        LlmStatus.Ready -> "LLM: ready"
        is LlmStatus.MissingModel -> "LLM: missing model"
        is LlmStatus.Error -> "LLM: error"
    }
}

private fun voiceStatusLabel(engine: com.ayushbot.app.voice.VoiceEngineType?, isSpeaking: Boolean): String {
    if (isSpeaking) return "Voice: speaking"
    return when (engine) {
        com.ayushbot.app.voice.VoiceEngineType.INDIC -> "Voice: Indic"
        com.ayushbot.app.voice.VoiceEngineType.ANDROID -> "Voice: Android"
        null -> "Voice: ready"
    }
}

@Composable
private fun VoiceReadinessCard(
    languageLabel: String,
    message: String,
    modelsReady: Boolean,
    canDownload: Boolean,
    isDownloading: Boolean,
    downloadProgress: Int,
    onDownload: () -> Unit,
) {
    val spacing = AyushBotDesignSystem.spacing

    Surface(
        shape = MaterialTheme.shapes.large,
        color = if (modelsReady) {
            MaterialTheme.colorScheme.surfaceContainerLow
        } else {
            MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.55f)
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(spacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Voice language: $languageLabel",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.height(spacing.xs))
                    Text(
                        text = message,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                if (canDownload && !modelsReady) {
                    AssistChip(
                        onClick = onDownload,
                        enabled = !isDownloading,
                        label = {
                            Text(if (isDownloading) "$downloadProgress%" else "Download")
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun ChatBubble(message: ChatMessage) {
    val spacing = AyushBotDesignSystem.spacing
    val maxWidth = LocalConfiguration.current.screenWidthDp.dp * 0.82f

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (message.isUser) Alignment.End else Alignment.Start,
    ) {
        Surface(
            modifier = Modifier.widthIn(max = maxWidth),
            shape = MaterialTheme.shapes.large,
            color = if (message.isUser) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.surfaceContainerHigh
            },
            tonalElevation = if (message.isUser) 0.dp else 1.dp,
        ) {
            Column(modifier = Modifier.padding(spacing.md)) {
                Text(
                    text = message.text,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (message.isUser) {
                        MaterialTheme.colorScheme.onPrimary
                    } else {
                        MaterialTheme.colorScheme.onSurface
                    },
                )

                if (message.citation != null) {
                    Spacer(Modifier.height(spacing.sm))
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.55f),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            Icon(
                                Icons.AutoMirrored.Rounded.MenuBook,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(14.dp),
                            )
                            Text(
                                text = message.citation,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Medium,
                            )
                        }
                    }
                }
            }
        }
    }
}
