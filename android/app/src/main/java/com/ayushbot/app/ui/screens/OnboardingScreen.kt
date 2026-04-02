package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowForward
import androidx.compose.material.icons.rounded.Translate
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ═══════════════════════════════════════════════════════════════
// OnboardingScreen — 3-step first-launch flow:
// 1. Language Selection (13 Indian languages)
// 2. ASHA Profile Setup
// 3. Gateway Pairing
// ═══════════════════════════════════════════════════════════════

data class LanguageOption(
    val code: String,
    val nameNative: String,
    val nameEnglish: String,
    val script: String,
)

private val languages = listOf(
    LanguageOption("hi", "हिन्दी", "Hindi", "देवनागरी"),
    LanguageOption("bn", "বাংলা", "Bengali", "বাংলা"),
    LanguageOption("ta", "தமிழ்", "Tamil", "தமிழ்"),
    LanguageOption("te", "తెలుగు", "Telugu", "తెలుగు"),
    LanguageOption("kn", "ಕನ್ನಡ", "Kannada", "ಕನ್ನಡ"),
    LanguageOption("mr", "मराठी", "Marathi", "देवनागरी"),
    LanguageOption("gu", "ગુજરાતી", "Gujarati", "ગુજરાતી"),
    LanguageOption("pa", "ਪੰਜਾਬੀ", "Punjabi", "ਗੁਰਮੁਖੀ"),
    LanguageOption("or", "ଓଡ଼ିଆ", "Odia", "ଓଡ଼ିଆ"),
    LanguageOption("ml", "മലയാളം", "Malayalam", "മലയാളം"),
    LanguageOption("as", "অসমীয়া", "Assamese", "অসমীয়া"),
    LanguageOption("ur", "اردو", "Urdu", "نستعلیق"),
    LanguageOption("en", "English", "English", "Latin"),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OnboardingScreen(
    onComplete: () -> Unit,
) {
    var step by remember { mutableIntStateOf(0) }
    var selectedLanguage by remember { mutableStateOf<String?>(null) }
    var ashaName by remember { mutableStateOf("") }
    var ashaId by remember { mutableStateOf("") }
    var phcName by remember { mutableStateOf("") }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Progress indicator
            LinearProgressIndicator(
                progress = { (step + 1) / 3f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp),
                color = MaterialTheme.colorScheme.primary,
                trackColor = MaterialTheme.colorScheme.surfaceVariant,
            )

            AnimatedContent(
                targetState = step,
                transitionSpec = {
                    (slideInHorizontally { it } + fadeIn()) togetherWith
                            (slideOutHorizontally { -it } + fadeOut())
                },
                label = "onboarding_step",
            ) { currentStep ->
                when (currentStep) {
                    0 -> LanguageSelectionStep(
                        selectedLanguage = selectedLanguage,
                        onSelect = { selectedLanguage = it },
                        onNext = { step = 1 },
                    )
                    1 -> ProfileSetupStep(
                        ashaName = ashaName,
                        onNameChange = { ashaName = it },
                        ashaId = ashaId,
                        onIdChange = { ashaId = it },
                        phcName = phcName,
                        onPhcChange = { phcName = it },
                        onNext = { step = 2 },
                        onBack = { step = 0 },
                    )
                    2 -> GatewayPairingStep(
                        onComplete = onComplete,
                        onBack = { step = 1 },
                    )
                }
            }
        }
    }
}

@Composable
private fun LanguageSelectionStep(
    selectedLanguage: String?,
    onSelect: (String) -> Unit,
    onNext: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        Spacer(Modifier.height(32.dp))

        Icon(
            imageVector = Icons.Rounded.Translate,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(48.dp),
        )

        Spacer(Modifier.height(16.dp))

        Text(
            text = "Choose Your Language",
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )

        Text(
            text = "अपनी भाषा चुनें",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(24.dp))

        LazyVerticalGrid(
            columns = GridCells.Adaptive(minSize = 140.dp),
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            items(languages) { lang ->
                val isSelected = selectedLanguage == lang.code
                Card(
                    onClick = { onSelect(lang.code) },
                    modifier = Modifier.heightIn(min = 92.dp),
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(
                        containerColor = if (isSelected) {
                            MaterialTheme.colorScheme.primaryContainer
                        } else {
                            MaterialTheme.colorScheme.surface
                        }
                    ),
                    border = if (isSelected) {
                        BorderStroke(2.dp, MaterialTheme.colorScheme.primary)
                    } else {
                        BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                    },
                    elevation = CardDefaults.cardElevation(0.dp),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text(
                            text = lang.nameNative,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                            textAlign = TextAlign.Center,
                        )
                        Spacer(Modifier.height(2.dp))
                        Text(
                            text = lang.nameEnglish,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center,
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        Button(
            onClick = onNext,
            enabled = selectedLanguage != null,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = MaterialTheme.shapes.extraLarge,
        ) {
            Text("Continue", style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.width(8.dp))
            Icon(Icons.AutoMirrored.Rounded.ArrowForward, contentDescription = null)
        }
    }
}

@Composable
private fun ProfileSetupStep(
    ashaName: String,
    onNameChange: (String) -> Unit,
    ashaId: String,
    onIdChange: (String) -> Unit,
    phcName: String,
    onPhcChange: (String) -> Unit,
    onNext: () -> Unit,
    onBack: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        Spacer(Modifier.height(32.dp))

        Text(
            text = "ASHA Profile",
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.onSurface,
        )

        Text(
            text = "Set up your worker profile",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = ashaName,
            onValueChange = onNameChange,
            label = { Text("Full Name") },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = ashaId,
            onValueChange = onIdChange,
            label = { Text("ASHA ID (from NHM registration)") },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = phcName,
            onValueChange = onPhcChange,
            label = { Text("Assigned PHC") },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.weight(1f))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            OutlinedButton(
                onClick = onBack,
                modifier = Modifier
                    .weight(1f)
                    .height(56.dp),
                shape = MaterialTheme.shapes.extraLarge,
            ) {
                Text("Back")
            }

            Button(
                onClick = onNext,
                enabled = ashaName.isNotBlank() && ashaId.isNotBlank(),
                modifier = Modifier
                    .weight(1f)
                    .height(56.dp),
                shape = MaterialTheme.shapes.extraLarge,
            ) {
                Text("Continue")
                Spacer(Modifier.width(8.dp))
                Icon(Icons.AutoMirrored.Rounded.ArrowForward, contentDescription = null, modifier = Modifier.size(18.dp))
            }
        }
    }
}

@Composable
private fun GatewayPairingStep(
    onComplete: () -> Unit,
    onBack: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(48.dp))

        // Pulsing scanning animation
        Box(
            modifier = Modifier
                .size(120.dp)
                .clip(RoundedCornerShape(60.dp))
                .background(MaterialTheme.colorScheme.primaryContainer),
            contentAlignment = Alignment.Center,
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(48.dp),
                color = MaterialTheme.colorScheme.primary,
                strokeWidth = 4.dp,
            )
        }

        Spacer(Modifier.height(32.dp))

        Text(
            text = "Scanning for PHC Gateway...",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface,
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.height(8.dp))

        Text(
            text = "Make sure you're connected to the PHC Wi-Fi network",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.height(32.dp))

        // Simulated found gateway
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.large,
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer,
            ),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Surface(
                    modifier = Modifier.size(8.dp),
                    shape = RoundedCornerShape(4.dp),
                    color = com.ayushbot.app.ui.theme.StateGreen,
                ) {}
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "AyushBot Gateway",
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(
                        text = "PHC Mawlynnong · Connected",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = onComplete,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = MaterialTheme.shapes.extraLarge,
        ) {
            Text("Get Started", style = MaterialTheme.typography.labelLarge, fontSize = 16.sp)
        }

        Spacer(Modifier.height(8.dp))

        TextButton(onClick = onComplete) {
            Text("Skip — Work Offline", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
