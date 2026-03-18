package com.ayushbot.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
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
    SymptomItem("stridor", "Stridor at Rest", Icons.Rounded.VolumeUp, "Respiratory"),
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
    var currentStep by remember { mutableIntStateOf(0) }
    var patientName by remember { mutableStateOf("") }
    var patientAge by remember { mutableStateOf("") }
    var patientSex by remember { mutableStateOf("Female") }
    var selectedSymptoms by remember { mutableStateOf(setOf<String>()) }

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
                    .padding(horizontal = 16.dp, vertical = 12.dp),
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
                        Spacer(Modifier.height(4.dp))
                        Text(
                            label,
                            style = MaterialTheme.typography.labelSmall,
                            color = if (index <= currentStep) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }

            // Step connector line
            LinearProgressIndicator(
                progress = { (currentStep.toFloat()) / (stepLabels.size - 1) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp)
                    .height(2.dp),
                color = MaterialTheme.colorScheme.primary,
                trackColor = MaterialTheme.colorScheme.surfaceVariant,
            )

            Spacer(Modifier.height(8.dp))

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
                    1 -> SensorCaptureStep()
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
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
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
                            if (currentStep < 3) {
                                currentStep++
                                if (currentStep == 3) {
                                    // Simulate analysis, then navigate to recommendation
                                }
                            }
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(56.dp),
                        shape = MaterialTheme.shapes.extraLarge,
                    ) {
                        Text(if (currentStep == 2) "Submit" else "Continue")
                        Spacer(Modifier.width(8.dp))
                        Icon(
                            if (currentStep == 2) Icons.Rounded.Send else Icons.AutoMirrored.Rounded.ArrowForward,
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
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
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
private fun SensorCaptureStep() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
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
                value = 96f,
                maxValue = 100f,
                unit = "%",
                label = "SpO₂",
                ringColor = spo2RingColor(96f),
                signalQuality = 0.92f,
            )
            VitalGauge(
                value = 128f,
                maxValue = 200f,
                unit = "BPM",
                label = "Heart Rate",
                ringColor = hrRingColor(128f),
                signalQuality = 0.85f,
            )
            VitalGauge(
                value = 38.2f,
                maxValue = 42f,
                unit = "°C",
                label = "Temp",
                ringColor = tempRingColor(38.2f),
                signalQuality = 1f,
                size = 100.dp,
            )
        }

        Spacer(Modifier.height(24.dp))

        // Weight input
        OutlinedTextField(
            value = "8.2",
            onValueChange = { },
            label = { Text("Weight (kg)") },
            leadingIcon = { Icon(Icons.Rounded.Scale, null) },
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.medium,
            singleLine = true,
        )

        Spacer(Modifier.height(24.dp))

        // Record button
        Button(
            onClick = { },
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
            Text("Record Vitals", style = MaterialTheme.typography.labelLarge)
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
            columns = GridCells.Fixed(2),
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(bottom = 8.dp),
        ) {
            val groups = symptoms.groupBy { it.group }
            groups.forEach { (groupName, groupSymptoms) ->
                item(span = { GridItemSpan(2) }) {
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
