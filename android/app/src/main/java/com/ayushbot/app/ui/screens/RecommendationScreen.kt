package com.ayushbot.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Chat
import androidx.compose.material.icons.rounded.Description
import androidx.compose.material.icons.rounded.FormatListBulleted
import androidx.compose.material.icons.rounded.LocalHospital
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material.icons.rounded.Share
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.ActionPlanCard
import com.ayushbot.app.ui.components.ActionPlanStep
import com.ayushbot.app.ui.components.EmptyStateCard
import com.ayushbot.app.ui.components.ErrorStateCard
import com.ayushbot.app.ui.components.LoadingStateCard
import com.ayushbot.app.ui.components.OfflineStateCard
import com.ayushbot.app.ui.components.RiskBadge
import com.ayushbot.app.ui.components.RiskTier
import com.ayushbot.app.ui.components.VoicePlaybackButton
import com.ayushbot.app.ui.theme.AyushBotDesignSystem
import com.ayushbot.app.ui.theme.SourceTextStyle
import com.ayushbot.app.ui.theme.StateAmber
import com.ayushbot.app.ui.theme.StateDeepOrange

private data class RecommendationModel(
    val riskTier: RiskTier,
    val diagnosis: String,
    val confidence: Float,
    val confidenceLabel: String,
    val explanation: String,
    val evidenceText: String?,
    val evidenceSource: String?,
    val treatSteps: List<ActionPlanStep>,
    val referSteps: List<ActionPlanStep>,
    val counselSteps: List<ActionPlanStep>,
    val differentials: List<Pair<String, String>>,
)

private val sampleRecommendation = RecommendationModel(
    riskTier = RiskTier.HIGH,
    diagnosis = "Pneumonia (suspected)",
    confidence = 0.68f,
    confidenceLabel = "Likely",
    explanation = "Fast breathing with chest indrawing in a febrile child under 5 is consistent with pneumonia. Immediate referral is recommended.",
    evidenceText = "A child with cough or difficulty breathing who has chest indrawing should be classified as PNEUMONIA and referred.",
    evidenceSource = "IMCI Chart Booklet, Section 3.2, p. 42",
    treatSteps = listOf(
        ActionPlanStep("Give first amoxicillin dose", "250mg dispersible tablet crushed in breastmilk.", emphasize = true),
        ActionPlanStep("Monitor airway and breathing", "Keep child upright and reassess breathing every 10 minutes."),
        ActionPlanStep("Prepare transfer", "Do not delay referral after first dose."),
    ),
    referSteps = listOf(
        ActionPlanStep("Refer to Mawlynnong PHC", "Distance 4.2 km, estimated transfer time 25 minutes.", emphasize = true),
        ActionPlanStep("Call transport now", "Use ambulance/auto based on availability and urgency."),
        ActionPlanStep("Carry referral note", "Include vitals, symptoms, and first-dose timestamp."),
    ),
    counselSteps = listOf(
        ActionPlanStep("Continue breastfeeding", "Offer frequent feeds during transfer."),
        ActionPlanStep("Keep child warm", "Avoid exposure to cold wind during travel."),
        ActionPlanStep("Escalate immediately", "If breathing worsens, call 108 immediately."),
    ),
    differentials = listOf(
        "Bronchiolitis" to "Wheezing in infant with first respiratory episode.",
        "Severe Malaria" to "Fever plus respiratory distress in endemic area.",
    ),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecommendationScreen(
    onBack: () -> Unit,
) {
    val spacing = AyushBotDesignSystem.spacing
    val listState = rememberLazyListState()
    var isPlaying by remember { mutableStateOf(false) }
    var recommendationState by remember {
        mutableStateOf<ScreenUiState<RecommendationModel>>(ScreenUiState.Success(sampleRecommendation))
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Recommendation") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { }) {
                        Icon(Icons.Rounded.Share, "Share")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        when (val state = recommendationState) {
            ScreenUiState.Loading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(spacing.lg),
                ) {
                    LoadingStateCard(
                        title = "Preparing recommendation",
                        subtitle = "Synthesizing diagnosis and action plan from local evidence...",
                    )
                }
            }

            is ScreenUiState.Error -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(spacing.lg),
                ) {
                    ErrorStateCard(
                        title = "Recommendation unavailable",
                        subtitle = state.message,
                        onRetry = {
                            recommendationState = ScreenUiState.Success(sampleRecommendation)
                        },
                    )
                }
            }

            ScreenUiState.Empty -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(spacing.lg),
                ) {
                    EmptyStateCard(
                        title = "No recommendation yet",
                        subtitle = "Complete patient intake and vitals to generate recommendation.",
                    )
                }
            }

            is ScreenUiState.Success,
            is ScreenUiState.Offline -> {
                val data = when (state) {
                    is ScreenUiState.Success -> state.data
                    is ScreenUiState.Offline -> state.cachedData ?: sampleRecommendation
                    else -> sampleRecommendation
                }
                val isOffline = state is ScreenUiState.Offline

                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    state = listState,
                    verticalArrangement = Arrangement.spacedBy(spacing.md),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(bottom = spacing.xl),
                ) {
                    item { RiskBadge(tier = data.riskTier) }

                    item {
                        Column(
                            modifier = Modifier.padding(horizontal = spacing.lg),
                            verticalArrangement = Arrangement.spacedBy(spacing.md),
                        ) {
                            if (isOffline) {
                                OfflineStateCard(
                                    title = "Offline recommendation",
                                    subtitle = "Showing locally available guidance. Sync when gateway is reachable.",
                                )
                            }

                            if (data.confidence < 0.6f) {
                                Card(
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                                    shape = MaterialTheme.shapes.medium,
                                    elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = spacing.lg, vertical = spacing.md),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                                    ) {
                                        Icon(Icons.Rounded.Warning, contentDescription = null)
                                        Text(
                                            text = "Low confidence output. Follow protocol referral and reassessment steps.",
                                            style = MaterialTheme.typography.bodyMedium,
                                        )
                                    }
                                }
                            }

                            PrimaryDiagnosisCard(data = data)

                            ActionPlanCard(
                                title = "Treat Now",
                                icon = Icons.Rounded.Medication,
                                iconTint = StateAmber,
                                steps = data.treatSteps,
                                defaultExpanded = true,
                            )

                            ActionPlanCard(
                                title = "Refer To",
                                icon = Icons.Rounded.LocalHospital,
                                iconTint = MaterialTheme.colorScheme.primary,
                                steps = data.referSteps,
                                defaultExpanded = true,
                            )

                            ActionPlanCard(
                                title = "Counsel Caregiver",
                                icon = Icons.Rounded.Chat,
                                iconTint = StateDeepOrange,
                                steps = data.counselSteps,
                            )

                            EvidenceCard(data = data)

                            VoicePlaybackButton(
                                text = if (isPlaying) "Pause playback" else "Read Aloud in Hindi",
                                isPlaying = isPlaying,
                                onClick = { isPlaying = !isPlaying },
                            )

                            Row(
                                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                OutlinedButton(
                                    onClick = { },
                                    modifier = Modifier.weight(1f),
                                    shape = MaterialTheme.shapes.extraLarge,
                                ) {
                                    Icon(Icons.Rounded.Description, contentDescription = null, modifier = Modifier.size(18.dp))
                                    Spacer(Modifier.width(spacing.sm))
                                    Text("Referral Slip")
                                }

                                OutlinedButton(
                                    onClick = { },
                                    modifier = Modifier.weight(1f),
                                    shape = MaterialTheme.shapes.extraLarge,
                                ) {
                                    Icon(Icons.Rounded.Share, contentDescription = null, modifier = Modifier.size(18.dp))
                                    Spacer(Modifier.width(spacing.sm))
                                    Text("Share")
                                }
                            }

                            ActionPlanCard(
                                title = "Other Possible Diagnoses",
                                icon = Icons.Rounded.FormatListBulleted,
                                iconTint = MaterialTheme.colorScheme.onSurfaceVariant,
                                steps = data.differentials.map {
                                    ActionPlanStep(title = it.first, detail = it.second)
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PrimaryDiagnosisCard(
    data: RecommendationModel,
) {
    val spacing = AyushBotDesignSystem.spacing

    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .background(MaterialTheme.colorScheme.primary)
            )

            Column(modifier = Modifier.padding(spacing.lg)) {
                Text(
                    text = data.diagnosis,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )

                Spacer(Modifier.height(spacing.sm))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(spacing.xs),
                ) {
                    Text(
                        text = "Confidence:",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    repeat(3) { index ->
                        Card(
                            modifier = Modifier.size(8.dp),
                            shape = MaterialTheme.shapes.extraSmall,
                            colors = CardDefaults.cardColors(
                                containerColor = if (index < (data.confidence * 3).toInt().coerceAtLeast(1)) {
                                    StateAmber
                                } else {
                                    MaterialTheme.colorScheme.surfaceVariant
                                }
                            ),
                            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                        ) {}
                    }
                    Spacer(Modifier.width(spacing.xs))
                    Text(
                        text = data.confidenceLabel,
                        style = MaterialTheme.typography.labelSmall,
                        color = StateAmber,
                        fontWeight = FontWeight.SemiBold,
                    )
                }

                Spacer(Modifier.height(spacing.md))

                Text(
                    text = data.explanation,
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }
    }
}

@Composable
private fun EvidenceCard(
    data: RecommendationModel,
) {
    val spacing = AyushBotDesignSystem.spacing

    if (data.evidenceText == null || data.evidenceSource == null) {
        ErrorStateCard(
            title = "Evidence details unavailable",
            subtitle = "Follow protocol-safe referral steps while evidence panel is unavailable.",
            actionLabel = "Use Protocol",
            onRetry = { },
        )
        return
    }

    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.5.dp),
    ) {
        Column(modifier = Modifier.padding(spacing.lg)) {
            Text(
                text = "Evidence & Source",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(Modifier.height(spacing.sm))
            Text(
                text = "\"${data.evidenceText}\"",
                style = SourceTextStyle,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(Modifier.height(spacing.sm))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Spacer(Modifier.height(spacing.sm))
            Text(
                text = data.evidenceSource,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Medium,
            )
        }
    }
}
