package com.ayushbot.app.ui.screens

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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.MenuBook
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Sync
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.ErrorStateCard
import com.ayushbot.app.ui.components.OfflineStateCard
import com.ayushbot.app.ui.theme.AyushBotDesignSystem
import kotlinx.coroutines.delay

data class ChatMessage(
    val text: String,
    val isUser: Boolean,
    val citation: String? = null,
)

private val sampleConversation = listOf(
    ChatMessage("What is the correct dose of ORS for a 2-year-old with moderate dehydration?", isUser = true),
    ChatMessage(
        text = "For a 2-year-old child (~12 kg) with moderate dehydration:\n\n• Give 75 mL/kg of ORS solution over 4 hours\n• That's approximately 900 mL over 4 hours\n• Give frequent small sips using a cup\n• If vomiting occurs, wait 10 minutes then continue slowly.",
        isUser = false,
        citation = "IMCI Chart Booklet, Sect. 5, p. 78",
    ),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceQueryScreen(
    onBack: () -> Unit,
) {
    val spacing = AyushBotDesignSystem.spacing
    var inputText by remember { mutableStateOf("") }
    var micState by remember { mutableStateOf(VoiceMicState.IDLE) }
    var isOffline by remember { mutableStateOf(false) }
    val messages = remember { mutableStateListOf(*sampleConversation.toTypedArray()) }

    LaunchedEffect(micState) {
        if (micState == VoiceMicState.PROCESSING) {
            delay(1200)
            messages.add(
                ChatMessage(
                    text = "I heard your query and processed it locally. You can continue with referral-safe guidance while offline.",
                    isUser = false,
                    citation = "Offline protocol mode",
                )
            )
            micState = VoiceMicState.IDLE
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
                actions = {
                    AssistChip(
                        onClick = { isOffline = !isOffline },
                        label = {
                            Text(if (isOffline) "Offline" else "Online")
                        },
                        leadingIcon = {
                            Icon(Icons.Rounded.Sync, contentDescription = null, modifier = Modifier.size(16.dp))
                        },
                    )
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
                            onClick = {
                                micState = when (micState) {
                                    VoiceMicState.IDLE -> VoiceMicState.LISTENING
                                    VoiceMicState.LISTENING -> VoiceMicState.PROCESSING
                                    VoiceMicState.PROCESSING -> VoiceMicState.PROCESSING
                                    VoiceMicState.ERROR -> VoiceMicState.IDLE
                                }
                            },
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
                            onValueChange = { inputText = it },
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
                                        messages.add(ChatMessage(inputText, isUser = true))
                                        inputText = ""
                                        micState = VoiceMicState.PROCESSING
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
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
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

            if (micState == VoiceMicState.ERROR) {
                item {
                    ErrorStateCard(
                        title = "Voice processing failed",
                        subtitle = "Please retry voice input or type your question.",
                        onRetry = { micState = VoiceMicState.IDLE },
                    )
                }
            }

            items(messages) { message ->
                ChatBubble(message = message)
            }

            if (micState == VoiceMicState.PROCESSING) {
                item {
                    ChatBubble(
                        message = ChatMessage(
                            text = "Thinking...",
                            isUser = false,
                        )
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
                                Icons.Rounded.MenuBook,
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
