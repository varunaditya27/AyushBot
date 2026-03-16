package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.VolumeUp
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.RiskBadge
import com.ayushbot.app.ui.components.RiskTier
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// RecommendationScreen — The payoff screen.
// Risk Badge → Diagnosis Card → Action Plan → Voice Playback
// ═══════════════════════════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecommendationScreen(
    onBack: () -> Unit,
) {
    val scrollState = rememberScrollState()

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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(scrollState),
        ) {
            // ─── Section A: Risk Badge (Full-width) ───
            RiskBadge(tier = RiskTier.HIGH)

            Spacer(Modifier.height(16.dp))

            Column(
                modifier = Modifier.padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // ─── Section B: Primary Diagnosis Card ───
                Card(
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                    elevation = CardDefaults.cardElevation(1.dp),
                ) {
                    Column {
                        // Teal accent strip
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(4.dp)
                                .background(MaterialTheme.colorScheme.primary)
                        )

                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                "Pneumonia (suspected)",
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                            )

                            Spacer(Modifier.height(8.dp))

                            // Confidence indicator — 3 dots
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp),
                            ) {
                                Text(
                                    "Confidence:",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Spacer(Modifier.width(4.dp))
                                repeat(3) { i ->
                                    Surface(
                                        modifier = Modifier.size(8.dp),
                                        shape = MaterialTheme.shapes.extraSmall,
                                        color = if (i < 2) StateAmber else MaterialTheme.colorScheme.surfaceVariant,
                                    ) {}
                                }
                                Spacer(Modifier.width(4.dp))
                                Text(
                                    "Likely",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = StateAmber,
                                    fontWeight = FontWeight.SemiBold,
                                )
                            }

                            Spacer(Modifier.height(12.dp))

                            Text(
                                "Fast breathing with chest indrawing in a febrile child under 5 is consistent with pneumonia. Immediate referral recommended.",
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurface,
                            )

                            Spacer(Modifier.height(12.dp))

                            // Citation in Noto Serif
                            Card(
                                shape = MaterialTheme.shapes.medium,
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                                ),
                            ) {
                                Row(modifier = Modifier.padding(12.dp)) {
                                    Box(
                                        modifier = Modifier
                                            .width(3.dp)
                                            .height(48.dp)
                                            .background(MaterialTheme.colorScheme.outlineVariant)
                                    )
                                    Spacer(Modifier.width(12.dp))
                                    Column {
                                        Text(
                                            "\"A child with cough or difficulty breathing who has chest indrawing should be classified as PNEUMONIA and referred.\"",
                                            style = SourceTextStyle,
                                            color = MaterialTheme.colorScheme.onSurface,
                                        )
                                        Spacer(Modifier.height(4.dp))
                                        Text(
                                            "— IMCI Chart Booklet, Section 3.2, p. 42",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.primary,
                                            fontWeight = FontWeight.Medium,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                // ─── Section C: Action Plan — Expandable Cards ───
                ActionCard(
                    title = "Treat Now",
                    icon = Icons.Rounded.Medication,
                    iconTint = StateGreen,
                ) {
                    Text(
                        "Amoxicillin Dispersible Tablet",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Dose: 250mg (1 tablet) crushed in breastmilk",
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    Text(
                        "Route: Oral • Every 8 hours • For 5 days",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Give first dose before referral",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = StateDeepOrange,
                    )
                }

                ActionCard(
                    title = "Refer To",
                    icon = Icons.Rounded.LocalHospital,
                    iconTint = MaterialTheme.colorScheme.primary,
                    defaultExpanded = true,
                ) {
                    Text(
                        "Mawlynnong PHC",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.height(4.dp))
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        AssistChip(
                            onClick = { },
                            label = { Text("4.2 km") },
                            leadingIcon = { Icon(Icons.Rounded.DirectionsWalk, null, modifier = Modifier.size(16.dp)) },
                            shape = MaterialTheme.shapes.small,
                        )
                        AssistChip(
                            onClick = { },
                            label = { Text("~25 min") },
                            leadingIcon = { Icon(Icons.Rounded.Schedule, null, modifier = Modifier.size(16.dp)) },
                            shape = MaterialTheme.shapes.small,
                        )
                    }
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Transport: Auto/Ambulance recommended for child with respiratory distress",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }

                ActionCard(
                    title = "Counsel Mother",
                    icon = Icons.Rounded.Chat,
                    iconTint = TertiaryLight,
                ) {
                    val messages = listOf(
                        "Continue breastfeeding frequently",
                        "Keep the child warm and dry",
                        "Return immediately if breathing becomes worse or the child stops eating",
                    )
                    messages.forEachIndexed { i, msg ->
                        Row(
                            modifier = Modifier.padding(vertical = 4.dp),
                        ) {
                            Text(
                                "${i + 1}.",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                msg,
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                    }
                }

                // ─── Section D: Voice Playback Button ───
                Button(
                    onClick = { },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = MaterialTheme.shapes.extraLarge,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                    ),
                ) {
                    Icon(Icons.AutoMirrored.Rounded.VolumeUp, null)
                    Spacer(Modifier.width(8.dp))
                    Text("🔊 सुनें — Read Aloud in Hindi", style = MaterialTheme.typography.labelLarge)
                }

                // ─── Section E: Referral Slip Button ───
                OutlinedButton(
                    onClick = { },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = MaterialTheme.shapes.extraLarge,
                ) {
                    Icon(Icons.Rounded.Description, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Generate Referral Slip (PDF)")
                }

                // ─── Section F: Differential Diagnoses (Collapsed) ───
                ActionCard(
                    title = "Other Possible Diagnoses",
                    icon = Icons.Rounded.FormatListBulleted,
                    iconTint = MaterialTheme.colorScheme.onSurfaceVariant,
                ) {
                    listOf(
                        "Bronchiolitis" to "Wheezing in infant with first respiratory episode",
                        "Severe Malaria" to "Fever + respiratory distress in endemic area",
                    ).forEach { (name, desc) ->
                        Column(modifier = Modifier.padding(vertical = 4.dp)) {
                            Text(
                                name,
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(
                                desc,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                        if (name == "Bronchiolitis") {
                            HorizontalDivider(
                                modifier = Modifier.padding(vertical = 4.dp),
                                color = MaterialTheme.colorScheme.outlineVariant,
                            )
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))
            }
        }
    }
}

@Composable
private fun ActionCard(
    title: String,
    icon: ImageVector,
    iconTint: androidx.compose.ui.graphics.Color,
    defaultExpanded: Boolean = false,
    content: @Composable ColumnScope.() -> Unit,
) {
    var expanded by remember { mutableStateOf(defaultExpanded) }

    Card(
        onClick = { expanded = !expanded },
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(0.5.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(
                    icon, null,
                    tint = iconTint,
                    modifier = Modifier.size(24.dp),
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f),
                )
                Icon(
                    if (expanded) Icons.Rounded.ExpandLess else Icons.Rounded.ExpandMore,
                    contentDescription = if (expanded) "Collapse" else "Expand",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            AnimatedVisibility(
                visible = expanded,
                enter = expandVertically(
                    animationSpec = spring(dampingRatio = 0.85f, stiffness = 300f)
                ) + fadeIn(),
                exit = shrinkVertically() + fadeOut(),
            ) {
                Column(modifier = Modifier.padding(top = 12.dp)) {
                    content()
                }
            }
        }
    }
}
