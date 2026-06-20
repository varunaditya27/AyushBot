package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.ArrowForward
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.automirrored.rounded.VolumeUp
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.*
import com.ayushbot.app.ui.theme.*
import kotlinx.coroutines.delay

// ═══════════════════════════════════════════════════════════════
// NewVisitScreen — Multi-step triage wizard with progress stepper
// Step 1: Patient Identity  Step 2: Sensor Capture
// Step 3: Symptom Checklist Step 4: Analyzing...
// ═══════════════════════════════════════════════════════════════

private val stepLabels = listOf("Patient", "Vitals", "Symptoms", "Analyzing")

data class SymptomItem(
    val id: String,
    val label: String,
    val icon: ImageVector,
    val group: String,
)

private val symptomList = listOf(
    // Respiratory
    SymptomItem("fast_breathing", "Fast Breathing", Icons.Rounded.Air, "Respiratory"),
    SymptomItem("chest_indrawing", "Chest Indrawing", Icons.Rounded.Compress, "Respiratory"),
    SymptomItem("stridor", "Stridor at Rest", Icons.AutoMirrored.Rounded.VolumeUp, "Respiratory"),
    // Danger Signs
    SymptomItem("convulsions", "Convulsions", Icons.Rounded.ElectricBolt, "Danger Signs"),
    SymptomItem("unable_drink", "Unable to Drink", Icons.Rounded.WaterDrop, "Danger Signs"),
    SymptomItem("lethargic", "Lethargic", Icons.Rounded.Hotel, "Danger Signs"),
    SymptomItem("vomiting", "Vomiting Everything", Icons.Rounded.Sick, "Danger Signs"),
    // Nutrition
    SymptomItem("wasting", "Severe Wasting", Icons.Rounded.MonitorWeight, "Nutrition"),
    SymptomItem("edema", "Bilateral Edema", Icons.Rounded.WaterDrop, "Nutrition"),
    SymptomItem("pallor", "Pallor / Anemia", Icons.Rounded.Opacity, "Nutrition"),
    // Fever & Diarrhea
    SymptomItem("fever_7days", "Fever > 7 Days", Icons.Rounded.Thermostat, "Fever & Diarrhea"),
    SymptomItem("stiff_neck", "Stiff Neck", Icons.Rounded.PersonOff, "Fever & Diarrhea"),
    SymptomItem("rash", "Measles Rash", Icons.Rounded.Coronavirus, "Fever & Diarrhea"),
    SymptomItem("diarrhea", "Diarrhea", Icons.Rounded.Warning, "Fever & Diarrhea"),
    SymptomItem("sunken_eyes", "Sunken Eyes", Icons.Rounded.Visibility, "Fever & Diarrhea"),
    SymptomItem("skin_pinch", "Skin Pinch Slow", Icons.Rounded.TouchApp, "Fever & Diarrhea"),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewVisitScreen(
    onBack: () -> Unit,
    onComplete: () -> Unit,
) {
    val spacing = AyushBotDesignSystem.spacing
    var currentStep by remember { mutableIntStateOf(0) }
    var patientName by remember { mutableStateOf("") }
    var patientAge by remember { mutableStateOf("") }
    var patientSex by remember { mutableStateOf("Female") }
    var selectedSymptoms by remember { mutableStateOf(setOf<String>()) }
    var sensorQualityOk by remember { mutableStateOf(false) }

    val canProceed = when (currentStep) {
        0 -> patientName.isNotBlank() && patientAge.toIntOrNull() != null
        1 -> sensorQualityOk
        2 -> selectedSymptoms.isNotEmpty()
        else -> true
    }

    if (currentStep == 3) {
        LaunchedEffect(Unit) {
            delay(1800)
            onComplete()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("New Visit") },
                navigationIcon = {
                    IconButton(onClick = {
                        if (currentStep > 0) currentStep-- else onBack()
                    }) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, "Back")
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
                .padding(padding),
        ) {
            // ─── Step Progress Indicator ───
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = spacing.lg, vertical = spacing.md),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                stepLabels.forEachIndexed { index, label ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.weight(1f),
                    ) {
                        Surface(
                            modifier = Modifier.size(32.dp),
                            shape = MaterialTheme.shapes.extraLarge,
                            color = when {
                                index < currentStep -> MaterialTheme.colorScheme.primary
                                index == currentStep -> MaterialTheme.colorScheme.primary
                                else -> MaterialTheme.colorScheme.surfaceVariant
                            },
                        ) {
                            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                                if (index < currentStep) {
                                    Icon(
                                        Icons.Rounded.Check, null,
                                        tint = MaterialTheme.colorScheme.onPrimary,
                                        modifier = Modifier.size(16.dp),
                                    )
                                } else {
                                    Text(
                                        "${index + 1}",
                                        style = MaterialTheme.typography.labelSmall,
                                        fontWeight = FontWeight.Bold,
                                        color = if (index == currentStep) MaterialTheme.colorScheme.onPrimary
                                        else MaterialTheme.colorScheme.onSurfaceVariant,
                                    )
                                }
                            }
                        }
                        Spacer(Modifier.height(spacing.xs))
                        Text(
                            label,
                            style = MaterialTheme.typography.labelSmall,
                            color = if (index <= currentStep) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }

            Spacer(Modifier.height(spacing.sm))

            // ─── Step Content ───
            AnimatedContent(
                targetState = currentStep,
                transitionSpec = {
                    (slideInHorizontally { it } + fadeIn()) togetherWith
                            (slideOutHorizontally { -it } + fadeOut())
                },
                label = "visit_step",
                modifier = Modifier.weight(1f),
            ) { step ->
                when (step) {
                    0 -> PatientIdentityStep(
                        name = patientName, onNameChange = { patientName = it },
                        age = patientAge, onAgeChange = { patientAge = it },
                        sex = patientSex, onSexChange = { patientSex = it },
                    )
                    1 -> SensorCaptureStep(
                        isOffline = false,
                        onSignalQualityChanged = { sensorQualityOk = it },
                    )
                    2 -> SymptomChecklistStep(
                        symptoms = symptomList,
                        selected = selectedSymptoms,
                        onToggle = { id ->
                            selectedSymptoms = if (id in selectedSymptoms) {
                                selectedSymptoms - id
                            } else {
                                selectedSymptoms + id
                            }
                        },
                    )
                    3 -> AnalyzingStep()
                }
            }

            // ─── Navigation Buttons ───
            if (currentStep < 3) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(spacing.lg),
                    horizontalArrangement = Arrangement.spacedBy(spacing.md),
                ) {
                    if (currentStep > 0) {
                        OutlinedButton(
                            onClick = { currentStep-- },
                            modifier = Modifier
                                .weight(1f)
                                .height(56.dp),
                            shape = MaterialTheme.shapes.extraLarge,
                        ) {
                            Text("Back")
                        }
                    }

                    Button(
                        onClick = {
                            if (canProceed && currentStep < 3) {
                                currentStep++
                            }
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(56.dp),
                        shape = MaterialTheme.shapes.extraLarge,
                        enabled = canProceed,
                    ) {
                        Text(if (currentStep == 2) "Submit" else "Continue")
                        Spacer(Modifier.width(spacing.sm))
                        Icon(
                            if (currentStep == 2) Icons.AutoMirrored.Rounded.Send else Icons.AutoMirrored.Rounded.ArrowForward,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PatientIdentityStep(
    name: String, onNameChange: (String) -> Unit,
    age: String, onAgeChange: (String) -> Unit,
    sex: String, onSexChange: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .imePadding()
            .padding(16.dp),
    ) {
        Text(
            "Patient Details",
            style = MaterialTheme.typography.headlineSmall,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            "Search existing or enter new patient",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(24.dp))

        OutlinedTextField(
            value = name,
            onValueChange = onNameChange,
            label = { Text("Patient Name or ABHA ID") },
            leadingIcon = { Icon(Icons.Rounded.Search, null) },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = age,
            onValueChange = onAgeChange,
            label = { Text("Age (months)") },
            leadingIcon = { Icon(Icons.Rounded.CalendarMonth, null) },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(8.dp))

        // Age group label
        val ageMonths = age.toIntOrNull()
        if (ageMonths != null) {
            val ageGroup = when {
                ageMonths <= 1 -> "Neonate (0-28 days)"
                ageMonths <= 12 -> "Infant (1-12 months)"
                else -> "Child (1-5 years)"
            }
            Surface(
                shape = MaterialTheme.shapes.small,
                color = MaterialTheme.colorScheme.primaryContainer,
            ) {
                Text(
                    ageGroup,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // Sex selection
        Text("Sex", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("Male", "Female").forEach { option ->
                FilterChip(
                    selected = sex == option,
                    onClick = { onSexChange(option) },
                    label = { Text(option) },
                    leadingIcon = if (sex == option) {
                        { Icon(Icons.Rounded.Check, null, modifier = Modifier.size(18.dp)) }
                    } else null,
                    shape = MaterialTheme.shapes.small,
                )
            }
        }
    }
}

@Composable
private fun SensorCaptureStep(
    isOffline: Boolean,
    onSignalQualityChanged: (Boolean) -> Unit,
) {
    val spo2Value = 96f
    val hrValue = 128f
    val tempValue = 38.2f
    val weightKg = "8.2"

    val signalQualitySpo2 = 0.92f
    val signalQualityHr = 0.85f
    val signalQualityTemp = 1f
    val minimumQuality = minOf(signalQualitySpo2, signalQualityHr, signalQualityTemp)
    val qualityGatePassed = minimumQuality >= 0.8f
    val criticalDetected = spo2Value < 90f || tempValue >= 39.5f

    LaunchedEffect(qualityGatePassed) {
        onSignalQualityChanged(qualityGatePassed)
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (isOffline) {
            OfflineStateCard(
                title = "Gateway unavailable",
                subtitle = "Capturing vitals in offline mode. You can continue safely.",
                modifier = Modifier.padding(bottom = 12.dp),
            )
        }

        // BLE connection banner
        Card(
            shape = MaterialTheme.shapes.medium,
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer,
            ),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    Icons.Rounded.BluetoothConnected,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "Sensor Pack Connected — Reading vitals...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
        }

        Spacer(Modifier.height(32.dp))

        // ─── Three Circular Vitals Gauges ───
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            VitalGauge(
                value = spo2Value,
                maxValue = 100f,
                unit = "%",
                label = "SpO₂",
                ringColor = spo2RingColor(spo2Value),
                signalQuality = signalQualitySpo2,
            )
            VitalGauge(
                value = hrValue,
                maxValue = 200f,
                unit = "BPM",
                label = "Heart Rate",
                ringColor = hrRingColor(hrValue),
                signalQuality = signalQualityHr,
            )
            VitalGauge(
                value = tempValue,
                maxValue = 42f,
                unit = "°C",
                label = "Temp",
                ringColor = tempRingColor(tempValue),
                signalQuality = signalQualityTemp,
                size = 100.dp,
            )
        }

        Spacer(Modifier.height(24.dp))

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.padding(top = 8.dp),
        ) {
            SignalQualityIndicator(quality = minimumQuality)
            Text(
                text = if (qualityGatePassed) "Reading quality: Good" else "Reading quality: Improve sensor placement",
                style = MaterialTheme.typography.bodySmall,
                color = if (qualityGatePassed) StateGreen else StateAmber,
            )
        }

        // Weight input
        OutlinedTextField(
            value = weightKg,
            onValueChange = { },
            label = { Text("Weight (kg)") },
            leadingIcon = { Icon(Icons.Rounded.Scale, null) },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(24.dp))

        if (criticalDetected) {
            ErrorStateCard(
                title = "Critical vitals detected",
                subtitle = "Trigger emergency referral immediately before continuing routine flow.",
                actionLabel = "Emergency Referral",
                onRetry = { },
                modifier = Modifier.padding(bottom = 12.dp),
            )
        }

        // Record button
        Button(
            onClick = { },
            enabled = qualityGatePassed,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = MaterialTheme.shapes.extraLarge,
            colors = ButtonDefaults.buttonColors(
                containerColor = StateGreen,
            ),
        ) {
            Icon(Icons.Rounded.FiberManualRecord, null, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(8.dp))
            Text(
                if (qualityGatePassed) "Record Vitals" else "Adjust sensor position",
                style = MaterialTheme.typography.labelLarge,
            )
        }
    }
}

@Composable
private fun SymptomChecklistStep(
    symptoms: List<SymptomItem>,
    selected: Set<String>,
    onToggle: (String) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
    ) {
        // Voice add button
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
        ) {
            Text(
                "Select Symptoms",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.weight(1f),
            )
            FilledTonalIconButton(onClick = { }) {
                Icon(Icons.Rounded.Mic, "Voice Add Symptom")
            }
        }

        Spacer(Modifier.height(4.dp))

        Text(
            "${selected.size} symptom${if (selected.size != 1) "s" else ""} selected",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 16.dp),
        )

        Spacer(Modifier.height(12.dp))

        // Group symptoms and display
        LazyVerticalGrid(
            columns = GridCells.Adaptive(minSize = 160.dp),
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(bottom = 8.dp),
        ) {
            val groups = symptoms.groupBy { it.group }
            groups.forEach { (groupName, groupSymptoms) ->
                item(span = { GridItemSpan(maxLineSpan) }) {
                    Text(
                        groupName,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 8.dp, bottom = 4.dp, start = 4.dp),
                    )
                }
                items(groupSymptoms, key = { it.id }) { symptom ->
                    SymptomCard(
                        icon = symptom.icon,
                        label = symptom.label,
                        isSelected = symptom.id in selected,
                        onClick = { onToggle(symptom.id) },
                    )
                }
            }
        }
    }
}

@Composable
private fun AnalyzingStep() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(32.dp),
        ) {
            // Pulsing analysis animation
            CircularProgressIndicator(
                modifier = Modifier.size(64.dp),
                color = MaterialTheme.colorScheme.primary,
                strokeWidth = 5.dp,
            )

            Spacer(Modifier.height(32.dp))

            Text(
                "Analyzing Patient Data...",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface,
            )

            Spacer(Modifier.height(8.dp))

            Text(
                "Running clinical triage through AyushBot AI",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(48.dp))

            // Skeleton shimmer for upcoming cards
            repeat(3) {
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(if (it == 0) 96.dp else 72.dp)
                        .padding(vertical = 4.dp),
                    shape = MaterialTheme.shapes.large,
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                ) {}
            }
        }
    }
}
