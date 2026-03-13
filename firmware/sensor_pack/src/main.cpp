// =============================================================================
// AyushBot Sensor Pack — Arduino Entry Point
// =============================================================================
//
// PURPOSE:
//   This is the main Arduino sketch file — the entry point for the sensor pack
//   firmware. It contains the standard setup() and loop() functions that
//   orchestrate the entire sensor pack lifecycle.
//
// RESPONSIBILITIES:
//
//   setup():
//     1. Initialize serial port for debug logging (115200 baud)
//     2. Initialize all sensor drivers (MAX30100, DS18B20, HX711)
//     3. Initialize the Kalman filter with default state estimates
//     4. Load the TFLite Micro model into the tensor arena
//     5. Initialize the BLE GATT service and start advertising
//     6. Initialize the ASCON-128 encryption context with the pre-shared key
//     7. Set up hardware alarm pins (buzzer, LED) as outputs
//     8. Run a self-test sequence: verify each sensor returns valid data,
//        confirm TinyML model is loaded, confirm BLE is advertising
//
//   loop():
//     Runs continuously at approximately SENSOR_READ_INTERVAL_MS cadence:
//     1. Read raw values from all three sensors
//     2. Check signal quality (variance-based filter on SpO2 readings —
//        if variance exceeds threshold, flag as invalid and prompt re-measure)
//     3. Feed valid readings into the Kalman filter to produce fused,
//        noise-reduced vital sign estimates
//     4. Compute delta values (ΔSpO2 and ΔHR over the last 30 seconds)
//     5. Assemble the 6-feature input vector for the TinyML classifier:
//        [SpO2, HR, Temperature, Age_months, ΔSpO2, ΔHR]
//     6. Run TinyML inference — if DANGER detected:
//        a. Activate hardware alarm (buzzer + LED)
//        b. Set the DangerFlag BLE characteristic to 1
//     7. Encrypt the vital signs payload using ASCON-128 AEAD
//     8. Update BLE GATT characteristics with the encrypted payload
//     9. If a connected BLE central (phone) is present, send notification
//
// STATE MANAGEMENT:
//   - Patient age is received once from the Android phone via a BLE write
//     characteristic at the start of each clinical encounter.
//   - A circular buffer of the last 30 seconds of SpO2 and HR readings is
//     maintained for delta computation.
//   - The alarm state latches ON until explicitly reset by the ASHA via BLE
//     or a physical button press (safety design: alarm never auto-clears).
//
// POWER MANAGEMENT:
//   - Between sensor reads, the MCU enters a low-power idle state.
//   - BLE advertising uses the minimum feasible interval to save battery.
//   - Target: 11+ hours of continuous monitoring on a standard LiPo cell.
//
// ERROR HANDLING:
//   - If a sensor fails to initialize, the system logs the failure over
//     serial, disables that sensor's BLE characteristic, and continues
//     operating with the remaining sensors (graceful degradation).
//   - If the TinyML model fails to load, the system falls back to pure
//     threshold-based alarming using the clinical thresholds in config.h.
// =============================================================================
