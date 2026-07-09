package com.ayushbot.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.BatteryStd
import androidx.compose.material.icons.rounded.BluetoothConnected
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.components.ErrorStateCard
import com.ayushbot.app.ui.components.SignalQualityIndicator
import com.ayushbot.app.ui.components.VitalGauge
import com.ayushbot.app.ui.components.hrRingColor
import com.ayushbot.app.ui.components.spo2RingColor
import com.ayushbot.app.ui.components.tempRingColor
import com.ayushbot.app.ui.theme.AyushBotDesignSystem
import com.ayushbot.app.ui.theme.StateGreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SensorManagementScreen(
    onBack: () -> Unit,
) {
    val container = com.ayushbot.app.core.di.LocalAppContainer.current
    val sensorRepository = container.sensorRepository
    val sensorData by sensorRepository.sensorData.collectAsState()

    androidx.compose.runtime.LaunchedEffect(Unit) {
        sensorRepository.startCapture()
    }

    val spacing = AyushBotDesignSystem.spacing
    val selfTestPassed = sensorData.isSelfTestPassed
    val signalQuality = sensorData.signalQuality
    val isConnected = sensorData.isConnected

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sensor Management") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { sensorRepository.startCapture() }) {
                        Icon(Icons.Rounded.Refresh, "Refresh")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(spacing.lg),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            item {
                Card(
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                    ),
                    elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(spacing.lg),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        Icon(Icons.Rounded.BluetoothConnected, contentDescription = null)
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = if (isConnected) "Sensor pack connected" else "Sensor pack disconnected",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(
                                text = sensorData.deviceName,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer,
                            )
                        }
                        Icon(
                            imageVector = Icons.Rounded.CheckCircle,
                            contentDescription = null,
                            tint = StateGreen,
                        )
                    }
                }
            }

            item {
                Text(
                    text = "Live Vitals",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                ) {
                    VitalGauge(
                        value = sensorData.spo2,
                        maxValue = 100f,
                        unit = "%",
                        label = "SpO₂",
                        ringColor = spo2RingColor(sensorData.spo2),
                        signalQuality = signalQuality,
                    )
                    VitalGauge(
                        value = sensorData.hr,
                        maxValue = 200f,
                        unit = "BPM",
                        label = "HR",
                        ringColor = hrRingColor(sensorData.hr),
                        signalQuality = signalQuality,
                    )
                    VitalGauge(
                        value = sensorData.tempC,
                        maxValue = 42f,
                        unit = "°C",
                        label = "Temp",
                        ringColor = tempRingColor(sensorData.tempC),
                        signalQuality = signalQuality,
                        size = 100.dp,
                    )
                }
            }

            item {
                Card(
                    shape = MaterialTheme.shapes.large,
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(spacing.lg),
                        verticalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                        ) {
                            Icon(Icons.Rounded.BatteryStd, contentDescription = null)
                            Text("Battery: ${sensorData.battery}%", style = MaterialTheme.typography.bodyLarge)
                        }

                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                        ) {
                            SignalQualityIndicator(signalQuality)
                            Text(
                                text = "Signal quality: Good",
                                style = MaterialTheme.typography.bodyMedium,
                                color = StateGreen,
                            )
                        }
                    }
                }
            }

            item {
                Button(
                    onClick = { sensorRepository.runSelfTest() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = MaterialTheme.shapes.extraLarge,
                ) {
                    Text("Run Sensor Self-Test")
                }
            }

            item {
                when (selfTestPassed) {
                    true -> Card(
                        shape = MaterialTheme.shapes.large,
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                    ) {
                        Column(modifier = Modifier.padding(spacing.lg)) {
                            Text("Self-test complete", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                            Spacer(Modifier.height(spacing.xs))
                            Text("All sensors healthy. Capture flow is safe to proceed.", style = MaterialTheme.typography.bodyMedium)
                        }
                    }

                    false -> ErrorStateCard(
                        title = "Self-test failed",
                        subtitle = "Check sensor cables and retry pairing before capture.",
                        onRetry = { sensorRepository.runSelfTest() },
                    )

                    null -> OutlinedButton(
                        onClick = { },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = MaterialTheme.shapes.extraLarge,
                    ) {
                        Text("Open Calibration Guide")
                    }
                }
            }
        }
    }
}
