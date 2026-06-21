// =============================================================================
// AyushBot Sensor Pack — main.cpp
// Hardware: ESP32 + MAX30102 + DS18B20 + HX711(5kg) + I2C LCD + Red/Green LED
// =============================================================================

#include <Arduino.h>
#include "config.h"
#include "sensors/max30102.h"
#include "sensors/ds18b20.h"
#include "sensors/hx711.h"
#include "fusion/kalman.h"
#include "tinyml/inference.h"
#include "comms/ascon_crypto.h"
#include "comms/ble_gatt.h"
#include "comms/lcd_display.h"

// =============================================================================
// Module instances
// =============================================================================
static MAX30102Sensor  g_maxSensor;
static DS18B20Sensor   g_tempSensor;
static HX711Sensor     g_weightSensor;
static KalmanFilter    g_kalman;
static InferenceEngine g_inference;
static AsconCrypto     g_crypto;
static BLEGattServer   g_ble;
static LCDDisplay      g_lcd;

// =============================================================================
// State
// =============================================================================
static volatile uint16_t g_patientAgeMos = 24;
static float g_spo2History[DELTA_BUFFER_SIZE] = {0};
static float g_hrHistory[DELTA_BUFFER_SIZE]   = {0};
static uint8_t g_histIdx   = 0;
static uint8_t g_histCount = 0;
static bool    g_alarmLatched = false;

static uint32_t g_lastSensorReadMs  = 0;
static uint32_t g_lastInferenceMs   = 0;
static uint32_t g_lastBleNotifyMs   = 0;
static uint32_t g_lastLcdUpdateMs   = 0;

// =============================================================================
// LED Helpers — separate Red and Green LEDs
// =============================================================================
static void ledGreen()   { digitalWrite(PIN_LED_GREEN, HIGH); digitalWrite(PIN_LED_RED, LOW); }
static void ledRed()     { digitalWrite(PIN_LED_GREEN, LOW);  digitalWrite(PIN_LED_RED, HIGH); }
static void ledBoth()    { digitalWrite(PIN_LED_GREEN, HIGH); digitalWrite(PIN_LED_RED, HIGH); }
static void ledOff()     { digitalWrite(PIN_LED_GREEN, LOW);  digitalWrite(PIN_LED_RED, LOW); }

// Blink red for advertising state
static void ledBlinkRed() {
    static bool state = false;
    static uint32_t last = 0;
    if (millis() - last > 500) { state = !state; digitalWrite(PIN_LED_RED, state); last = millis(); }
}

// =============================================================================
// Alarm
// =============================================================================
static void triggerAlarm(float spo2, float hr) {
    if (!g_alarmLatched) {
        g_alarmLatched = true;
        Serial.println("[ALARM] *** DANGER DETECTED ***");
        digitalWrite(PIN_BUZZER, HIGH);
        ledRed();
        g_ble.setDangerFlag(true);
        g_lcd.showDanger(spo2, hr);
    }
}

static void clearAlarm() {
    g_alarmLatched = false;
    digitalWrite(PIN_BUZZER, LOW);
    ledGreen();
    g_ble.setDangerFlag(false);
    Serial.println("[ALARM] Cleared");
}

static float computeDelta(float* history, uint8_t count) {
    if (count < 2) return 0.0f;
    float oldest = history[(g_histIdx - count + DELTA_BUFFER_SIZE) % DELTA_BUFFER_SIZE];
    float newest = history[(g_histIdx - 1  + DELTA_BUFFER_SIZE) % DELTA_BUFFER_SIZE];
    return newest - oldest;
}

// =============================================================================
// setup()
// =============================================================================
void setup() {
    Serial.begin(115200);
    Serial.println("\n========================================");
    Serial.println(" AyushBot Sensor Pack Booting...");
    Serial.println("========================================");

    // Pins
    pinMode(PIN_LED_GREEN,    OUTPUT);
    pinMode(PIN_LED_RED,      OUTPUT);
    pinMode(PIN_BUZZER,       OUTPUT);
    pinMode(PIN_RESET_BUTTON, INPUT_PULLUP);
    ledBoth();  // Both LEDs on during boot

    // LCD first — show boot message
    g_lcd.init();
    g_lcd.showStatus("AyushBot v1.0", "Booting...");

    // Sensors
    bool maxOk    = g_maxSensor.init();
    bool tempOk   = g_tempSensor.init();
    bool weightOk = g_weightSensor.init();

    if (!maxOk)    { Serial.println("[WARN] MAX30102 unavailable"); }
    if (!tempOk)   { Serial.println("[WARN] DS18B20 unavailable"); }
    if (!weightOk) { Serial.println("[WARN] HX711 unavailable"); }

    // Kalman filter
    g_kalman.init();

    // TinyML
    bool mlOk = g_inference.init();
    if (!mlOk) Serial.println("[WARN] TFLite failed — threshold fallback active");

    // BLE
    g_ble.onAgeWrittenCb = [](uint16_t ageMos) {
        g_patientAgeMos = ageMos;
        Serial.printf("[Main] Patient age: %d months\n", ageMos);
    };
    g_ble.init();

    // ASCON encryption
    const uint8_t psk[] = ASCON_PSK;
    g_crypto.init(psk);

    // Alarm off
    digitalWrite(PIN_BUZZER, LOW);

    // Ready
    ledOff();
    ledBlinkRed();  // Start blinking red = advertising
    g_lcd.showStatus("BLE: Advertising", "Place finger...");
    Serial.println("[AyushBot] Boot complete");
}

// =============================================================================
// loop()
// =============================================================================
void loop() {
    uint32_t now = millis();

    // -------------------------------------------------------------------------
    // 1. Read sensors
    // -------------------------------------------------------------------------
    if (now - g_lastSensorReadMs >= SENSOR_READ_INTERVAL_MS) {
        g_lastSensorReadMs = now;

        g_maxSensor.update();
        g_tempSensor.update();
        g_weightSensor.update();

        g_ble.setSignalQuality(g_maxSensor.getSignalQuality());

        // -----------------------------------------------------------------------
        // 2. Kalman fusion
        // -----------------------------------------------------------------------
        g_kalman.predict();
        if (g_maxSensor.getSignalQuality() == SIGNAL_GOOD && g_maxSensor.isValid()) {
            g_kalman.update(SPO2, g_maxSensor.getSpO2());
            g_kalman.update(HR,   g_maxSensor.getHeartRate());
        }
        if (g_tempSensor.isValid()) {
            g_kalman.update(TEMP, g_tempSensor.getTemperature());
        }

        float spo2, hr, temp;
        g_kalman.getState(spo2, hr, temp);

        // -----------------------------------------------------------------------
        // 3. Delta buffer
        // -----------------------------------------------------------------------
        g_spo2History[g_histIdx] = spo2;
        g_hrHistory[g_histIdx]   = hr;
        g_histIdx = (g_histIdx + 1) % DELTA_BUFFER_SIZE;
        if (g_histCount < DELTA_BUFFER_SIZE) g_histCount++;

        float deltaSpo2 = computeDelta(g_spo2History, g_histCount);
        float deltaHr   = computeDelta(g_hrHistory,   g_histCount);

        Serial.printf("[Vitals] SpO2=%.1f%% HR=%.0fbpm Temp=%.2f°C Weight=%.2fkg\n",
            spo2, hr, temp, g_weightSensor.getWeight());

        // -----------------------------------------------------------------------
        // 4. TinyML inference
        // -----------------------------------------------------------------------
        if (now - g_lastInferenceMs >= TINYML_INFERENCE_INTERVAL_MS) {
            g_lastInferenceMs = now;

            float features[MODEL_INPUT_FEATURES] = {
                spo2, hr, temp, (float)g_patientAgeMos, deltaSpo2, deltaHr
            };
            DangerResult result = g_inference.runInference(features);
            if (result.isDanger) triggerAlarm(spo2, hr);
        }

        // -----------------------------------------------------------------------
        // 5. LCD update
        // -----------------------------------------------------------------------
        if (now - g_lastLcdUpdateMs >= LCD_UPDATE_INTERVAL_MS) {
            g_lastLcdUpdateMs = now;
            if (!g_alarmLatched) {
                if (g_maxSensor.getSignalQuality() == SIGNAL_NONE) {
                    g_lcd.showStatus("Place finger on", "MAX30102 sensor");
                } else {
                    g_lcd.showVitals(spo2, hr, temp, g_weightSensor.getWeight());
                }
            }
            // Show BLE status on LCD row 0 if not connected
            if (!g_ble.isConnected()) g_lcd.showBLEStatus(false);
        }

        // -----------------------------------------------------------------------
        // 6. ASCON encrypt + BLE notify
        // -----------------------------------------------------------------------
        if (now - g_lastBleNotifyMs >= BLE_NOTIFY_INTERVAL_MS) {
            g_lastBleNotifyMs = now;

            struct __attribute__((packed)) VitalsPayload {
                uint8_t  spo2;
                uint16_t hr;
                int16_t  tempX100;
                uint16_t weightGrams;
                uint8_t  dangerFlag;
                uint32_t timestampMs;
            } payload;

            payload.spo2        = (uint8_t)constrain((int)spo2, 0, 100);
            payload.hr          = (uint16_t)constrain((int)hr, 0, 300);
            payload.tempX100    = (int16_t)(temp * 100);
            payload.weightGrams = (uint16_t)(g_weightSensor.getWeight() * 1000);
            payload.dangerFlag  = g_alarmLatched ? 1 : 0;
            payload.timestampMs = now;

            uint8_t nonce[ASCON_NONCE_LEN];
            g_crypto.generateNonce(nonce);
            uint8_t encBuf[sizeof(VitalsPayload) + ASCON_TAG_LEN];
            size_t  encLen = g_crypto.encrypt(
                (uint8_t*)&payload, sizeof(payload),
                nullptr, 0, nonce, encBuf);

            g_ble.updateVitals(payload.spo2, payload.hr, temp,
                               payload.weightGrams, encBuf, encLen);
        }
    }

    // -------------------------------------------------------------------------
    // Reset button — clears alarm latch (active LOW)
    // -------------------------------------------------------------------------
    if (digitalRead(PIN_RESET_BUTTON) == LOW) {
        delay(50);
        if (digitalRead(PIN_RESET_BUTTON) == LOW) {
            clearAlarm();
            while (digitalRead(PIN_RESET_BUTTON) == LOW);
        }
    }

    // LED state when no alarm
    if (!g_alarmLatched) {
        if (g_ble.isConnected()) ledGreen();
        else ledBlinkRed();
    }

    delay(10);
}