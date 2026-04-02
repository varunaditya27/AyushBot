package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
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
import com.ayushbot.app.ui.components.EmptyStateCard
import com.ayushbot.app.ui.components.ErrorStateCard
import com.ayushbot.app.ui.components.LoadingStateCard
import com.ayushbot.app.ui.components.OfflineStateCard
import com.ayushbot.app.ui.components.RiskTier
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// CaseHistoryScreen — Searchable, filterable case list.
// Filter chips, sort options, risk badges, sync indicators.
// ═══════════════════════════════════════════════════════════════

data class CaseRecord(
    val id: String,
    val patientName: String,
    val age: String,
    val date: String,
    val time: String,
    val diagnosis: String,
    val riskTier: RiskTier,
    val isSynced: Boolean,
)

private val sampleRecords = listOf(
    CaseRecord("C001", "Priya Devi", "18 mo", "Mar 13", "2:30 PM", "Pneumonia (suspected)", RiskTier.HIGH, true),
    CaseRecord("C002", "Ram Kumar", "3 yr", "Mar 13", "1:15 PM", "Mild Diarrhea", RiskTier.LOW, true),
    CaseRecord("C003", "Sunita Bai", "8 mo", "Mar 13", "12:00 PM", "Severe Malnutrition", RiskTier.CRITICAL, false),
    CaseRecord("C004", "Anita Sharma", "2 yr", "Mar 13", "11:20 AM", "Fever — Monitor", RiskTier.MEDIUM, true),
    CaseRecord("C005", "Baby Lakshmi", "4 mo", "Mar 13", "10:45 AM", "Upper Respiratory Infection", RiskTier.LOW, true),
    CaseRecord("C006", "Rekha Patel", "14 mo", "Mar 13", "9:30 AM", "Dengue (suspected)", RiskTier.HIGH, false),
    CaseRecord("C007", "Meena Kumari", "5 yr", "Mar 12", "4:00 PM", "Malaria (confirmed)", RiskTier.HIGH, true),
    CaseRecord("C008", "Sita Ram", "11 mo", "Mar 12", "2:15 PM", "Healthy — Routine Check", RiskTier.LOW, true),
)

private val filterOptions = listOf("All", "Today", "This Week", "Unsynced", "Critical")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CaseHistoryScreen(
    onCaseClick: (String) -> Unit = {},
) {
    val spacing = AyushBotDesignSystem.spacing
    var searchQuery by remember { mutableStateOf("") }
    var activeFilter by remember { mutableStateOf("All") }
    var historyState by remember {
        mutableStateOf<ScreenUiState<List<CaseRecord>>>(ScreenUiState.Success(sampleRecords))
    }

    val sourceCases = when (val state = historyState) {
        is ScreenUiState.Success -> state.data
        is ScreenUiState.Offline -> state.cachedData.orEmpty()
        else -> emptyList()
    }

    val filteredCases = sourceCases.filter { case ->
        val matchesSearch = searchQuery.isBlank() ||
                case.patientName.contains(searchQuery, ignoreCase = true) ||
                case.diagnosis.contains(searchQuery, ignoreCase = true)

        val matchesFilter = when (activeFilter) {
            "Today" -> case.date == "Mar 13"
            "Unsynced" -> !case.isSynced
            "Critical" -> case.riskTier == RiskTier.CRITICAL
            else -> true
        }

        matchesSearch && matchesFilter
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Case History") },
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
                .padding(padding),
        ) {
            when (val state = historyState) {
                ScreenUiState.Loading -> {
                    LoadingStateCard(
                        title = "Loading case history",
                        subtitle = "Fetching latest local records...",
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = spacing.lg, vertical = spacing.sm),
                    )
                }

                is ScreenUiState.Error -> {
                    ErrorStateCard(
                        title = "Couldn’t load case history",
                        subtitle = state.message,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = spacing.lg, vertical = spacing.sm),
                        onRetry = { historyState = ScreenUiState.Success(sampleRecords) },
                    )
                }

                is ScreenUiState.Offline -> {
                    OfflineStateCard(
                        title = "Showing local records",
                        subtitle = state.message,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = spacing.lg, vertical = spacing.sm),
                    )
                }

                else -> Unit
            }

            // ─── Search Bar ───
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = { Text("Search by name or diagnosis") },
                leadingIcon = { Icon(Icons.Rounded.Search, null) },
                trailingIcon = {
                    if (searchQuery.isNotBlank()) {
                        IconButton(onClick = { searchQuery = "" }) {
                            Icon(Icons.Rounded.Clear, "Clear search")
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
                    .padding(horizontal = spacing.lg, vertical = spacing.sm),
                shape = MaterialTheme.shapes.extraLarge,
                singleLine = true,
            )

            // ─── Filter Chips ───
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = spacing.lg, vertical = spacing.xs),
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                items(filterOptions) { filter ->
                    FilterChip(
                        selected = activeFilter == filter,
                        onClick = { activeFilter = filter },
                        label = { Text(filter, style = MaterialTheme.typography.labelMedium) },
                        leadingIcon = if (activeFilter == filter) {
                            { Icon(Icons.Rounded.Check, null, modifier = Modifier.size(16.dp)) }
                        } else null,
                        shape = MaterialTheme.shapes.small,
                    )
                }
            }

            // ─── Results Count ───
            Text(
                "${filteredCases.size} case${if (filteredCases.size != 1) "s" else ""}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = spacing.lg, vertical = spacing.sm),
            )

            // ─── Case List ───
            if (filteredCases.isEmpty()) {
                EmptyStateCard(
                    title = "No matching cases",
                    subtitle = "Try different filters or start a new visit.",
                    actionLabel = "Start New Visit",
                    onAction = { },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = spacing.lg, vertical = spacing.sm),
                )
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(horizontal = spacing.lg, vertical = spacing.xs),
                    verticalArrangement = Arrangement.spacedBy(spacing.sm),
                ) {
                    itemsIndexed(filteredCases, key = { _, c -> c.id }) { _, record ->
                        CaseRecordCard(
                            record = record,
                            onClick = { onCaseClick(record.id) },
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CaseRecordCard(
    record: CaseRecord,
    onClick: () -> Unit,
) {
    val riskColor = when (record.riskTier) {
        RiskTier.LOW -> StateGreen
        RiskTier.MEDIUM -> StateAmber
        RiskTier.HIGH -> StateDeepOrange
        RiskTier.CRITICAL -> StateCrimson
    }

    Card(
        onClick = onClick,
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(0.5.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.Top,
        ) {
            // Risk dot with colored background
            Surface(
                modifier = Modifier.size(40.dp),
                shape = CircleShape,
                color = riskColor.copy(alpha = 0.15f),
            ) {
                Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                    Surface(
                        modifier = Modifier.size(12.dp),
                        shape = CircleShape,
                        color = riskColor,
                    ) {}
                }
            }

            Spacer(Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(
                        record.patientName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        record.time,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }

                Spacer(Modifier.height(2.dp))

                Text(
                    record.diagnosis,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                Spacer(Modifier.height(8.dp))

                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    // Age chip
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = MaterialTheme.colorScheme.surfaceVariant,
                    ) {
                        Text(
                            record.age,
                            style = MaterialTheme.typography.labelSmall,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        )
                    }

                    // Risk label chip
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = riskColor.copy(alpha = 0.15f),
                    ) {
                        Text(
                            record.riskTier.name,
                            style = MaterialTheme.typography.labelSmall,
                            color = riskColor,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        )
                    }

                    Spacer(Modifier.weight(1f))

                    // Sync status
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = if (record.isSynced) {
                            MaterialTheme.colorScheme.primaryContainer
                        } else {
                            MaterialTheme.colorScheme.surfaceVariant
                        },
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 4.dp),
                        ) {
                            Icon(
                                imageVector = if (record.isSynced) Icons.Rounded.CloudDone else Icons.Rounded.Sync,
                                contentDescription = if (record.isSynced) "Synced" else "Pending sync",
                                tint = if (record.isSynced) StateGreen else MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(14.dp),
                            )
                            Text(
                                text = if (record.isSynced) "Synced" else "Pending",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (record.isSynced) StateGreen else MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        }
    }
}
