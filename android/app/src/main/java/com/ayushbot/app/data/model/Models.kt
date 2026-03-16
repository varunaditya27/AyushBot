package com.ayushbot.app.data.model

import com.ayushbot.app.ui.components.RiskTier

// ═══════════════════════════════════════════════════════════════
// UI State Models — Sealed classes for clean UDF state management.
// Every screen observes one of these via ViewModel StateFlow.
// ═══════════════════════════════════════════════════════════════

/** Generic UI state following sealed class pattern */
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

/** Domain model for a triage case displayed in the UI */
data class TriageCase(
    val id: String,
    val patientName: String,
    val ageMonths: Int,
    val sex: String,
    val spo2: Float?,
    val heartRate: Float?,
    val temperature: Float?,
    val weight: Float?,
    val symptoms: List<String>,
    val riskTier: RiskTier,
    val diagnosis: String?,
    val isSynced: Boolean,
    val timestamp: Long,
)

/** Sensor reading from BLE pack */
data class SensorReading(
    val spo2: Float,
    val heartRate: Float,
    val temperature: Float,
    val signalQuality: Float, // 0..1
    val dangerFlag: Boolean = false,
    val timestamp: Long = System.currentTimeMillis(),
)

/** Gateway connection state */
data class GatewayStatus(
    val isConnected: Boolean,
    val phcName: String? = null,
    val lastSync: Long? = null,
)
