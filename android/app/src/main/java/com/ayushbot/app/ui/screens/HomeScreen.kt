package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.*
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// HomeScreen — ASHA's operational headquarters.
// Today's stats, quick actions, recent cases, mic FAB.
// Scannable in 2 seconds.
// ═══════════════════════════════════════════════════════════════

data class RecentCase(
    val patientName: String,
    val time: String,
    val diagnosis: String,
    val riskTier: RiskTier,
    val isSynced: Boolean,
)

private val sampleCases = listOf(
    RecentCase("Priya Devi", "2:30 PM", "Pneumonia (suspected)", RiskTier.HIGH, true),
    RecentCase("Ram Kumar", "1:15 PM", "Mild Diarrhea", RiskTier.LOW, true),
    RecentCase("Sunita Bai", "12:00 PM", "Severe Malnutrition", RiskTier.CRITICAL, false),
    RecentCase("Anita Sharma", "11:20 AM", "Fever — Monitor", RiskTier.MEDIUM, true),
    RecentCase("Baby Lakshmi", "10:45 AM", "Upper Respiratory Infection", RiskTier.LOW, true),
    RecentCase("Rekha Patel", "9:30 AM", "Dengue (suspected)", RiskTier.HIGH, false),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onNewVisit: () -> Unit,
    onCaseHistory: () -> Unit,
    onVoiceQuery: () -> Unit,
    onSettings: () -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "AyushBot",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            "Namaste, Kavita 🙏",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { }) {
                        Icon(
                            Icons.Rounded.Notifications,
                            contentDescription = "Notifications",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        floatingActionButton = {
            LargeFloatingActionButton(
                onClick = onNewVisit,
                shape = CircleShape,
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
            ) {
                Icon(
                    Icons.Rounded.Mic,
                    contentDescription = "New Visit",
                    modifier = Modifier.size(32.dp),
                )
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // ─── Today's Summary Bar ───
            item {
                Card(
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                    ),
                    elevation = CardDefaults.cardElevation(0.dp),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                    ) {
                        StatItem(value = "8", label = "Cases Today")
                        StatItem(value = "3", label = "Pending Sync")
                        StatItem(value = "2", label = "Critical")
                    }
                }
            }

            // ─── Connection Status Chips ───
            item {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    StatusChip(label = "Sensor Pack", isConnected = true)
                    StatusChip(label = "PHC Gateway", isConnected = true)
                }
            }

            // ─── Quick Action Grid (2×2) ───
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        QuickActionButton(
                            icon = Icons.Rounded.Add,
                            label = "New Visit",
                            onClick = onNewVisit,
                            modifier = Modifier.weight(1f),
                        )
                        QuickActionButton(
                            icon = Icons.Rounded.History,
                            label = "Case History",
                            onClick = onCaseHistory,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        QuickActionButton(
                            icon = Icons.Rounded.RecordVoiceOver,
                            label = "Voice Query",
                            onClick = onVoiceQuery,
                            modifier = Modifier.weight(1f),
                            containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                            contentColor = MaterialTheme.colorScheme.onTertiaryContainer,
                        )
                        QuickActionButton(
                            icon = Icons.Rounded.LocalHospital,
                            label = "Emergency",
                            onClick = { },
                            modifier = Modifier.weight(1f),
                            containerColor = MaterialTheme.colorScheme.errorContainer,
                            contentColor = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }

            // ─── Recent Cases Header ───
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "Recent Cases",
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.weight(1f),
                    )
                    TextButton(onClick = onCaseHistory) {
                        Text("See All")
                    }
                }
            }

            // ─── Recent Cases Feed ───
            itemsIndexed(sampleCases) { index, case ->
                AnimatedVisibility(
                    visible = true,
                    enter = fadeIn(
                        animationSpec = tween(300, delayMillis = index * 40)
                    ) + slideInVertically(
                        animationSpec = tween(300, delayMillis = index * 40),
                        initialOffsetY = { 12 }
                    ),
                ) {
                    CaseCard(case = case)
                }
            }
        }
    }
}

@Composable
private fun StatItem(value: String, label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onPrimaryContainer,
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
        )
    }
}

@Composable
private fun CaseCard(case: RecentCase) {
    val riskColor = when (case.riskTier) {
        RiskTier.LOW -> StateGreen
        RiskTier.MEDIUM -> StateAmber
        RiskTier.HIGH -> StateDeepOrange
        RiskTier.CRITICAL -> StateCrimson
    }

    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(1.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Risk color dot
            Surface(
                modifier = Modifier.size(12.dp),
                shape = CircleShape,
                color = riskColor,
            ) {}

            Spacer(Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = case.patientName,
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    text = case.diagnosis,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = case.time,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(4.dp))
                Icon(
                    imageVector = if (case.isSynced) Icons.Rounded.CloudDone else Icons.Rounded.CloudOff,
                    contentDescription = if (case.isSynced) "Synced" else "Pending",
                    tint = if (case.isSynced) StateGreen else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(16.dp),
                )
            }
        }
    }
}
