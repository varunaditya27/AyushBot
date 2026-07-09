package com.ayushbot.app.data.repository

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlin.random.Random

class MockSensorRepository : SensorRepository {
    private val _sensorData = MutableStateFlow(SensorData(deviceName = "Mock-AyushBot-SP"))
    override val sensorData: StateFlow<SensorData> = _sensorData.asStateFlow()

    private var job: Job? = null
    private val scope = CoroutineScope(Dispatchers.Default)

    override fun startCapture() {
        job?.cancel()
        _sensorData.update { it.copy(isConnected = true, battery = 82) }
        job = scope.launch {
            while (true) {
                delay(1000)
                _sensorData.update { data ->
                    val nextSpo2 = if (Random.nextFloat() > 0.05f) {
                        (95..99).random().toFloat()
                    } else {
                        (88..94).random().toFloat()
                    }
                    val nextHr = (70..130).random().toFloat()
                    val nextTemp = 36.5f + Random.nextFloat() * 1.8f
                    val nextWeight = 8.2f + Random.nextFloat() * 0.1f
                    val nextQuality = 0.82f + Random.nextFloat() * 0.15f
                    data.copy(
                        spo2 = nextSpo2,
                        hr = nextHr,
                        tempC = nextTemp,
                        weightKg = nextWeight,
                        signalQuality = nextQuality
                    )
                }
            }
        }
    }

    override fun stopCapture() {
        job?.cancel()
        job = null
        _sensorData.update { it.copy(isConnected = false, spo2 = 0f, hr = 0f, tempC = 0f, weightKg = 0f, signalQuality = 0f) }
    }

    override fun runSelfTest() {
        scope.launch {
            _sensorData.update { it.copy(isSelfTestPassed = null) }
            delay(1500)
            _sensorData.update { it.copy(isSelfTestPassed = true) }
        }
    }
}
