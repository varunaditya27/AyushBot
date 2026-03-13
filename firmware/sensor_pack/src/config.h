// =============================================================================
// AyushBot Sensor Pack — Global Configuration Header
// =============================================================================
//
// PURPOSE:
//   Central configuration file for the entire sensor pack firmware. All pin
//   assignments, clinical thresholds, timing constants, BLE service UUIDs,
//   and model parameters are defined here. No magic numbers should appear
//   anywhere else in the codebase — every configurable value lives in this
//   file.
//
// SECTIONS:
//
//   1. PIN DEFINITIONS
//      - MAX30100 I2C address + interrupt pin
//      - DS18B20 OneWire data pin
//      - HX711 data and clock pins
//      - Alarm buzzer and LED indicator pins
//
//   2. CLINICAL THRESHOLDS (from MIMIC-IV training + WHO IMCI guidelines)
//      - SPO2_CRITICAL_LOW:     SpO2 threshold below which DANGER fires (e.g., 90%)
//      - HR_CRITICAL_HIGH:      Heart rate upper bound for age group
//      - HR_CRITICAL_LOW:       Heart rate lower bound (bradycardia)
//      - TEMP_FEVER_THRESHOLD:  Temperature in Celsius indicating fever
//      - TEMP_HYPOTHERMIA:      Temperature threshold for hypothermia
//      - DELTA_SPO2_ALARM:      Rate-of-change threshold for SpO2 over 30 seconds
//      - DELTA_HR_ALARM:        Rate-of-change threshold for HR over 30 seconds
//
//   3. TIMING CONSTANTS
//      - SENSOR_READ_INTERVAL_MS:   How often to poll sensors (e.g., 1000 ms)
//      - KALMAN_UPDATE_INTERVAL_MS: How often to run Kalman filter fusion
//      - BLE_NOTIFY_INTERVAL_MS:    How often to push BLE GATT notifications
//      - TINYML_INFERENCE_INTERVAL_MS: How often to run the danger classifier
//      - SIGNAL_QUALITY_WINDOW_MS:  Window size for variance-based quality check
//
//   4. BLE GATT CONFIGURATION
//      - Service UUID for AyushBot vital signs service
//      - Characteristic UUIDs for SpO2, HR, Temp, Weight, DangerFlag
//      - BLE device name and advertising interval
//
//   5. TINYML MODEL PARAMETERS
//      - MODEL_INPUT_FEATURES:  Number of features fed to the decision tree (6)
//      - DANGER_THRESHOLD:      Classification threshold (set low at 0.32 to
//                               maximize sensitivity / recall over specificity)
//      - MODEL_ARENA_SIZE:      TFLite Micro tensor arena allocation in bytes
//
//   6. ASCON-128 ENCRYPTION PARAMETERS
//      - Key length and nonce length for ASCON-128 AEAD
//      - Pre-shared key identifier (actual key stored in secure element or
//        hardcoded for prototype; production uses key exchange)
//
// DESIGN NOTES:
//   - All thresholds are age-group-aware where applicable. The classifier
//     handles age internally, but alarm thresholds for HR differ for neonates
//     (0-28 days), infants (1-12 months), and children (1-5 years).
//   - The DANGER_THRESHOLD of 0.32 was calibrated against the MIMIC-IV test
//     set to achieve minimum sensitivity of 0.95 (i.e., catch 95%+ of true
//     emergencies, accepting higher false positive rate).
// =============================================================================
