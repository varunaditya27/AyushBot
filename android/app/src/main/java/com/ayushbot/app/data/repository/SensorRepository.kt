package com.ayushbot.app.data.repository

import kotlinx.coroutines.flow.StateFlow

data class SensorData(
    val isConnected: Boolean = false,
    val spo2: Float = 0f,
    val hr: Float = 0f,
    val tempC: Float = 0f,
    val weightKg: Float = 0f,
    val signalQuality: Float = 0f,
    val battery: Int = 100,
    val deviceName: String = "Unknown",
    val isSelfTestPassed: Boolean? = null
)

interface SensorRepository {
    val sensorData: StateFlow<SensorData>
    fun startCapture()
    fun stopCapture()
    fun runSelfTest()
}
