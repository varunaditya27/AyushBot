package com.ayushbot.app.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// VoiceQueryScreen — Chat-style RAG interface.
// ASHA asks free-standing clinical questions.
// Chat bubbles with citation chips, mic FAB.
// ═══════════════════════════════════════════════════════════════

data class ChatMessage(
    val text: String,
    val isUser: Boolean,
    val citation: String? = null,
)

private val sampleConversation = listOf(
    ChatMessage("What is the correct dose of ORS for a 2-year-old with moderate dehydration?", isUser = true),
    ChatMessage(
        text = "For a 2-year-old child (~12 kg) with moderate dehydration:\n\n" +
                "• Give 75 mL/kg of ORS solution over 4 hours\n" +
                "• That's approximately 900 mL (about 1 litre) over 4 hours\n" +
                "• Give frequent small sips using a cup\n" +
                "• If the child vomits, wait 10 minutes then continue more slowly\n\n" +
                "Reassess after 4 hours. If signs of dehydration persist, repeat ORS treatment.",
        isUser = false,
        citation = "IMCI Chart Booklet, Sect. 5, p. 78",
    ),
    ChatMessage("Can I give zinc alongside ORS?", isUser = true),
    ChatMessage(
        text = "Yes! Zinc should be given alongside ORS for all diarrhea cases:\n\n" +
                "• Age > 6 months: 20 mg zinc tablet once daily for 10-14 days\n" +
                "• Age < 6 months: 10 mg zinc daily for 10-14 days\n\n" +
                "Dissolve the tablet in breastmilk or clean water if the child cannot chew. Continue zinc even after diarrhea stops — it helps prevent future episodes.",
        isUser = false,
        citation = "WHO/UNICEF Joint Statement, 2004 • NLEM p. 18",
    ),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VoiceQueryScreen(
    onBack: () -> Unit,
) {
    var inputText by remember { mutableStateOf("") }
    val messages = remember { mutableStateListOf(*sampleConversation.toTypedArray()) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("AyushBot", style = MaterialTheme.typography.titleMedium)
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
            // ─── Input Bar ───
            Surface(
                tonalElevation = 3.dp,
                color = MaterialTheme.colorScheme.surface,
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    // Mic button
                    FloatingActionButton(
                        onClick = { },
                        modifier = Modifier.size(48.dp),
                        shape = CircleShape,
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.primary,
                        elevation = FloatingActionButtonDefaults.elevation(0.dp),
                    ) {
                        Icon(Icons.Rounded.Mic, "Voice input", modifier = Modifier.size(24.dp))
                    }

                    Spacer(Modifier.width(8.dp))

                    OutlinedTextField(
                        value = inputText,
                        onValueChange = { inputText = it },
                        placeholder = { Text("Type or speak your question...") },
                        modifier = Modifier.weight(1f),
                        shape = MaterialTheme.shapes.extraLarge,
                        singleLine = true,
                        trailingIcon = {
                            if (inputText.isNotBlank()) {
                                IconButton(onClick = {
                                    messages.add(ChatMessage(inputText, isUser = true))
                                    inputText = ""
                                }) {
                                    Icon(Icons.AutoMirrored.Rounded.Send, "Send", tint = MaterialTheme.colorScheme.primary)
                                }
                            }
                        },
                    )
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            reverseLayout = false,
        ) {
            items(messages) { message ->
                ChatBubble(message)
            }
        }
    }
}

@Composable
private fun ChatBubble(message: ChatMessage) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (message.isUser) Alignment.End else Alignment.Start,
    ) {
        Surface(
            modifier = Modifier.widthIn(max = 300.dp),
            shape = MaterialTheme.shapes.large,
            color = if (message.isUser) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.surfaceContainerHigh
            },
            tonalElevation = if (message.isUser) 0.dp else 1.dp,
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = message.text,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (message.isUser) {
                        MaterialTheme.colorScheme.onPrimary
                    } else {
                        MaterialTheme.colorScheme.onSurface
                    },
                )

                // Citation chip
                if (message.citation != null) {
                    Spacer(Modifier.height(8.dp))
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Icon(
                                Icons.Rounded.MenuBook,
                                null,
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(14.dp),
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                message.citation,
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
