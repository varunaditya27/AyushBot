#include "max30102.h"
#include "spo2_algorithm.h"     // SparkFun SpO2 algorithm

// =============================================================================
// MAX30102 — Pulse Oximetry + Heart Rate Driver
// =============================================================================

bool MAX30102Sensor::init() {
    Serial.println("[MAX30102] Initialising...");

    if (!_sensor.begin(Wire, I2C_SPEED_FAST)) {
        Serial.println("[MAX30102] FAILED — check SDA(21)/SCL(22) wiring");
        _initialised = false;
        return false;
    }

    // Configure sensor
    // Sample average: 4, Mode: SpO2, Sample rate: 100Hz, LED pulse width: 411us
    _sensor.setup(
        60,     // LED brightness (0=off, 255=max) — 60 works well for most fingers
        4,      // Sample average
        2,      // LED mode: 2 = Red + IR (SpO2 mode)
        100,    // Sample rate: 100 Hz
        411,    // Pulse width: 411µs (highest resolution)
        4096    // ADC range: 4096nA
    );

    _sensor.setPulseAmplitudeRed(0x0A);   // Red LED — low for proximity
    _sensor.setPulseAmplitudeIR(0x1F);    // IR LED — higher for SpO2

    _initialised = true;
    Serial.println("[MAX30102] OK");
    return true;
}

// -----------------------------------------------------------------------------
void MAX30102Sensor::update() {
    if (!_initialised) return;

    // Collect 100 samples into buffer (SparkFun algorithm needs 100 samples)
    // At 100Hz this takes 1 second — fits our SENSOR_READ_INTERVAL_MS
    for (int i = 0; i < 100; i++) {
        while (!_sensor.available()) _sensor.check();
        _redBuffer[i] = _sensor.getRed();
        _irBuffer[i]  = _sensor.getIR();
        _sensor.nextSample();
    }

    // Check finger presence using IR value
    if (_irBuffer[99] < MAX30102_IR_MIN_VALID) {
        _isValid       = false;
        _signalQuality = SIGNAL_NONE;
        Serial.println("[MAX30102] No finger detected");
        return;
    }

    // Run SparkFun SpO2 algorithm
    int32_t spo2Raw, heartRateRaw;
    int8_t  spo2Valid, hrValid;

    maxim_heart_rate_and_oxygen_saturation(
        _irBuffer, 100, _redBuffer,
        &spo2Raw, &spo2Valid,
        &heartRateRaw, &hrValid
    );

    if (spo2Valid && hrValid && spo2Raw > 50 && heartRateRaw > 20) {
        // Moving average smoothing
        _spo2Buffer[_bufIdx] = (float)spo2Raw;
        _hrBuffer[_bufIdx]   = (float)heartRateRaw;
        _bufIdx = (_bufIdx + 1) % MOVING_AVG_WINDOW;

        float spo2Sum = 0, hrSum = 0;
        for (int i = 0; i < MOVING_AVG_WINDOW; i++) {
            spo2Sum += _spo2Buffer[i];
            hrSum   += _hrBuffer[i];
        }
        _spO2      = spo2Sum / MOVING_AVG_WINDOW;
        _heartRate = hrSum   / MOVING_AVG_WINDOW;
        _isValid   = true;
    } else {
        _isValid = false;
    }

    _signalQuality = _assessSignalQuality();
}

// -----------------------------------------------------------------------------
float         MAX30102Sensor::getSpO2()          const { return _spO2; }
float         MAX30102Sensor::getHeartRate()     const { return _heartRate; }
bool          MAX30102Sensor::isValid()          const { return _isValid; }
SignalQuality MAX30102Sensor::getSignalQuality() const { return _signalQuality; }

// -----------------------------------------------------------------------------
SignalQuality MAX30102Sensor::_assessSignalQuality() {
    if (!_isValid) return SIGNAL_NONE;

    float mean = _spO2;
    float variance = 0.0f;
    for (int i = 0; i < MOVING_AVG_WINDOW; i++) {
        float diff = _spo2Buffer[i] - mean;
        variance += diff * diff;
    }
    variance /= MOVING_AVG_WINDOW;

    return (variance > SPO2_VARIANCE_THRESHOLD) ? SIGNAL_POOR : SIGNAL_GOOD;
}