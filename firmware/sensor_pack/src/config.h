#pragma once

// =============================================================================
// AyushBot Sensor Pack — Global Configuration Header
// Components: MAX30102, DS18B20, HX711 (5kg), I2C LCD, Red+Green LEDs
// =============================================================================

// -----------------------------------------------------------------------------
// 1. PIN DEFINITIONS
// -----------------------------------------------------------------------------

// MAX30102 — I2C (default ESP32: SDA=21, SCL=22)
#define MAX30102_I2C_ADDR       0x57
#define MAX30102_INT_PIN        34      // Optional interrupt (input-only pin)

// DS18B20 — OneWire single data pin (4.7kΩ pull-up resistor required)
#define DS18B20_ONE_WIRE_PIN    4

// HX711 — Load cell amplifier (5kg load cell)
#define HX711_DOUT_PIN          16
#define HX711_SCK_PIN           17

// LEDs — separate Red and Green (not RGB)
#define PIN_LED_GREEN           26
#define PIN_LED_RED             25

// Buzzer alarm
#define PIN_BUZZER              32

// Physical reset button (active LOW)
#define PIN_RESET_BUTTON        33

// I2C LCD (shares I2C bus with MAX30102 — SDA=21, SCL=22)
// LCD I2C address: 0x27 (most common) or 0x3F
#define LCD_I2C_ADDR            0x27
#define LCD_COLS                16
#define LCD_ROWS                2

// -----------------------------------------------------------------------------
// 2. CLINICAL THRESHOLDS (WHO IMCI + MIMIC-IV calibrated)
// -----------------------------------------------------------------------------

// SpO2 (%)
#define SPO2_CRITICAL_LOW       90.0f
#define SPO2_WARNING_LOW        94.0f

// Heart Rate (BPM)
#define HR_CRITICAL_HIGH        160.0f
#define HR_CRITICAL_LOW         50.0f
#define HR_WARNING_HIGH         120.0f
#define HR_WARNING_LOW          60.0f

// Temperature (°C)
#define TEMP_FEVER_THRESHOLD    38.0f
#define TEMP_HYPOTHERMIA        35.0f
#define TEMP_HYPERPYREXIA       41.5f

// Axillary correction (+0.5°C to estimate core temperature)
#define TEMP_AXILLARY_OFFSET    0.5f

// Delta thresholds over 30-second window
#define DELTA_SPO2_ALARM        5.0f
#define DELTA_HR_ALARM          20.0f

// MAX30102 IR minimum for valid finger contact
#define MAX30102_IR_MIN_VALID   50000

// Weight bounds — 5kg load cell
#define WEIGHT_MIN_KG           0.5f
#define WEIGHT_MAX_KG           5.0f    // 5kg load cell maximum

// -----------------------------------------------------------------------------
// 3. TIMING CONSTANTS (milliseconds)
// -----------------------------------------------------------------------------
#define SENSOR_READ_INTERVAL_MS         1000
#define KALMAN_UPDATE_INTERVAL_MS       1000
#define BLE_NOTIFY_INTERVAL_MS          1000
#define TINYML_INFERENCE_INTERVAL_MS    2000
#define LCD_UPDATE_INTERVAL_MS          1000    // Refresh LCD every 1 second

// Delta computation window
#define DELTA_WINDOW_SECONDS            30
#define DELTA_BUFFER_SIZE               30

// -----------------------------------------------------------------------------
// 4. BLE GATT CONFIGURATION
// -----------------------------------------------------------------------------
#define BLE_DEVICE_NAME                 "AyushBot-SensorPack"
#define BLE_SERVICE_UUID                "a7u5hb07-0001-1000-8000-00805f9b34fb"
#define BLE_CHAR_SPO2_UUID              "a7u5hb07-0002-1000-8000-00805f9b34fb"
#define BLE_CHAR_HR_UUID                "a7u5hb07-0003-1000-8000-00805f9b34fb"
#define BLE_CHAR_TEMP_UUID              "a7u5hb07-0004-1000-8000-00805f9b34fb"
#define BLE_CHAR_WEIGHT_UUID            "a7u5hb07-0005-1000-8000-00805f9b34fb"
#define BLE_CHAR_DANGER_UUID            "a7u5hb07-0006-1000-8000-00805f9b34fb"
#define BLE_CHAR_AGE_UUID               "a7u5hb07-0007-1000-8000-00805f9b34fb"
#define BLE_CHAR_SIGNAL_QUALITY_UUID    "a7u5hb07-0008-1000-8000-00805f9b34fb"

// -----------------------------------------------------------------------------
// 5. TINYML MODEL PARAMETERS
// -----------------------------------------------------------------------------
#define MODEL_INPUT_FEATURES            6
#define DANGER_THRESHOLD                0.32f
#define MODEL_ARENA_SIZE                (8 * 1024)

// -----------------------------------------------------------------------------
// 6. ASCON-128 ENCRYPTION PARAMETERS
// -----------------------------------------------------------------------------
#define ASCON_KEY_LEN                   16
#define ASCON_NONCE_LEN                 16
#define ASCON_TAG_LEN                   16
#define ASCON_PSK { \
    0xA7, 0xA5, 0xAB, 0x07, 0xDE, 0xAD, 0xBE, 0xEF, \
    0xCA, 0xFE, 0xBA, 0xBE, 0x01, 0x23, 0x45, 0x67  \
}
#define DEVICE_ID                       0xA7B07001UL

// -----------------------------------------------------------------------------
// 7. HX711 CALIBRATION (5kg load cell)
// -----------------------------------------------------------------------------
#define HX711_CALIBRATION_FACTOR        420.0f
#define HX711_AVERAGING_SAMPLES         10

// -----------------------------------------------------------------------------
// 8. SIGNAL QUALITY ENUM
// -----------------------------------------------------------------------------
enum SignalQuality : uint8_t {
    SIGNAL_GOOD = 0,
    SIGNAL_POOR = 1,
    SIGNAL_NONE = 2
};