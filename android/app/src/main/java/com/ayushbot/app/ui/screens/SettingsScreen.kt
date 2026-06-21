package com.ayushbot.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// SettingsScreen — Minimal, only what ASHAs need.
// Language, Gateway, Profile, Offline toggle, Sync, About.
// ═══════════════════════════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onOpenSensorManagement: () -> Unit = {},
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ayushbot_prefs", android.content.Context.MODE_PRIVATE) }
    var selectedLangCode by remember { mutableStateOf(prefs.getString("selected_language", "en") ?: "en") }
    val ashaName = remember { prefs.getString("asha_name", "Kavita Sharma") ?: "Kavita Sharma" }
    val ashaId = remember { prefs.getString("asha_id", "NHM-RJ-04523") ?: "NHM-RJ-04523" }
    val phcName = remember { prefs.getString("phc_name", "Mawlynnong PHC") ?: "Mawlynnong PHC" }

    var showLanguageDialog by remember { mutableStateOf(false) }
    var offlineMode by remember { mutableStateOf(false) }
    var darkMode by remember { mutableStateOf(false) }
    var statusMessage by remember { mutableStateOf<String?>(null) }

    val languageDisplayName = when (selectedLangCode) {
        "en" -> "English"
        "hi" -> "हिन्दी (Hindi)"
        "kn" -> "ಕನ್ನಡ (Kannada)"
        "te" -> "తెలుగు (Telugu)"
        "ta" -> "தமிழ் (Tamil)"
        "bn" -> "বাংলা (Bengali)"
        "mr" -> "मराठी (Marathi)"
        "gu" -> "ગુજરાતી (Gujarati)"
        "pa" -> "ਪੰਜਾਬੀ (Punjabi)"
        "or" -> "ଓଡ଼ିଆ (Odia)"
        "ml" -> "മലയാളം (Malayalam)"
        "as" -> "অসমীয়া (Assamese)"
        "ur" -> "اردو (Urdu)"
        else -> "English"
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
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
                .verticalScroll(rememberScrollState()),
        ) {
            if (statusMessage != null) {
                AssistChip(
                    onClick = { statusMessage = null },
                    label = { Text(statusMessage!!) },
                    leadingIcon = {
                        Icon(
                            Icons.Rounded.CheckCircle,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                        )
                    },
                    modifier = Modifier
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                )
            }

            // ─── ASHA Profile Section ───
            SettingsGroup(title = "Profile") {
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
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Surface(
                            modifier = Modifier.size(48.dp),
                            shape = MaterialTheme.shapes.extraLarge,
                            color = MaterialTheme.colorScheme.primary,
                        ) {
                            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                                Text(
                                    ashaName.firstOrNull()?.toString()?.uppercase() ?: "A",
                                    style = MaterialTheme.typography.titleLarge,
                                    color = MaterialTheme.colorScheme.onPrimary,
                                    fontWeight = FontWeight.Bold,
                                )
                            }
                        }
                        Spacer(Modifier.width(16.dp))
                        Column {
                            Text(
                                ashaName,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(
                                "ASHA ID: $ashaId",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                            )
                        }
                    }
                }
            }

            // ─── App Settings ───
            SettingsGroup(title = "App Settings") {
                SettingsItem(
                    icon = Icons.Rounded.Translate,
                    title = "Language",
                    subtitle = languageDisplayName,
                    onClick = { showLanguageDialog = true },
                )
                SettingsItem(
                    icon = Icons.Rounded.DarkMode,
                    title = "Dark Mode",
                    subtitle = if (darkMode) "On" else "Off",
                    trailing = {
                        Switch(
                            checked = darkMode,
                            onCheckedChange = {
                                darkMode = it
                                statusMessage = "Display preference saved locally."
                            },
                        )
                    },
                )
                SettingsItem(
                    icon = Icons.Rounded.WifiOff,
                    title = "Force Offline Mode",
                    subtitle = if (offlineMode) "Enabled — data won't sync" else "Disabled",
                    trailing = {
                        Switch(
                            checked = offlineMode,
                            onCheckedChange = {
                                offlineMode = it
                                statusMessage = if (it) {
                                    "Offline mode enabled. Sync will resume when disabled."
                                } else {
                                    "Offline mode disabled. Sync can resume."
                                }
                            },
                        )
                    },
                )
            }

            // ─── Gateway & Sync ───
            SettingsGroup(title = "Connection") {
                SettingsItem(
                    icon = Icons.Rounded.Router,
                    title = "PHC Gateway",
                    subtitle = "Connected — $phcName",
                    subtitleColor = StateGreen,
                    onClick = { },
                )
                SettingsItem(
                    icon = Icons.Rounded.Bluetooth,
                    title = "Sensor Pack",
                    subtitle = "AyushBot-SP-04A2 · Battery: 78%",
                    subtitleColor = StateGreen,
                    onClick = { },
                )
                SettingsItem(
                    icon = Icons.Rounded.Build,
                    title = "Sensor Management",
                    subtitle = "Run diagnostics, inspect signal quality",
                    onClick = onOpenSensorManagement,
                )
            }

            // ─── Data Sync Status ───
            SettingsGroup(title = "Data Sync") {
                SyncStatusRow(label = "Cases", lastSync = "2 min ago", count = "142 synced")
                SyncStatusRow(label = "Models", lastSync = "Mar 12", count = "v2.1.4")
                SyncStatusRow(label = "Facilities", lastSync = "Mar 11", count = "24 facilities")
            }

            // ─── About ───
            SettingsGroup(title = "About") {
                SettingsItem(
                    icon = Icons.Rounded.Info,
                    title = "AyushBot",
                    subtitle = "Version 0.1.0 · RVCE Bangalore",
                    onClick = { },
                )
                SettingsItem(
                    icon = Icons.Rounded.Security,
                    title = "Privacy Policy",
                    subtitle = "DPDPA 2023 compliant",
                    onClick = { },
                )
                SettingsItem(
                    icon = Icons.Rounded.Code,
                    title = "Open Source Licenses",
                    subtitle = "View third-party libraries",
                    onClick = { },
                )
            }

            Spacer(Modifier.height(32.dp))
        }
    }

    if (showLanguageDialog) {
        AlertDialog(
            onDismissRequest = { showLanguageDialog = false },
            title = { Text("Choose Language") },
            text = {
                val languagesList = listOf(
                    Pair("en", "English"),
                    Pair("hi", "हिन्दी (Hindi)"),
                    Pair("kn", "ಕನ್ನಡ (Kannada)"),
                    Pair("te", "తెలుగు (Telugu)"),
                    Pair("ta", "தமிழ் (Tamil)"),
                    Pair("bn", "বাংলা (Bengali)")
                )
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState())
                ) {
                    languagesList.forEach { (code, label) ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    selectedLangCode = code
                                    prefs.edit().putString("selected_language", code).apply()
                                    showLanguageDialog = false
                                    statusMessage = "Language preference set to $label"
                                }
                                .padding(vertical = 12.dp, horizontal = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = (selectedLangCode == code),
                                onClick = {
                                    selectedLangCode = code
                                    prefs.edit().putString("selected_language", code).apply()
                                    showLanguageDialog = false
                                    statusMessage = "Language preference set to $label"
                                }
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(text = label, style = MaterialTheme.typography.bodyLarge)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showLanguageDialog = false }) {
                    Text("Close")
                }
            }
        )
    }
}

@Composable
private fun SettingsGroup(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
    ) {
        Text(
            title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(bottom = 6.dp, start = 8.dp),
        )
        Card(
            shape = MaterialTheme.shapes.large,
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface,
            ),
            elevation = CardDefaults.cardElevation(0.5.dp),
        ) {
            Column {
                content()
            }
        }
    }
}

@Composable
private fun SettingsItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    subtitleColor: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurfaceVariant,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    Surface(
        onClick = onClick ?: { },
        color = MaterialTheme.colorScheme.surface,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(24.dp),
            )
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(
                    subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = subtitleColor,
                )
            }
            if (trailing != null) {
                trailing()
            } else if (onClick != null) {
                Icon(
                    Icons.Rounded.ChevronRight,
                    null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(20.dp),
                )
            }
        }
    }
}

@Composable
private fun SyncStatusRow(
    label: String,
    lastSync: String,
    count: String,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.weight(1f),
        )
        Column(horizontalAlignment = Alignment.End) {
            Text(
                count,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Medium,
            )
            Text(
                lastSync,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
