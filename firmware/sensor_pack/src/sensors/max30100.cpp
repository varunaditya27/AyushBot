// =============================================================================
// AyushBot Sensor Pack — MAX30100 Pulse Oximetry + Heart Rate Driver
// =============================================================================
//
// PURPOSE:
//   Hardware abstraction layer for the MAX30100 (or MAX30102) pulse oximetry
//   and heart rate sensor module. This driver encapsulates all I2C
//   communication, register configuration, raw signal acquisition, and basic
//   signal conditioning for the photoplethysmography (PPG) waveform.
//
// WHAT THE MAX30100 DOES:
//   The MAX30100 is an integrated pulse oximetry and heart rate sensor that
//   uses two LEDs (red and infrared) and a photodetector. By measuring the
//   ratio of absorbed red vs infrared light passing through tissue, it
//   derives peripheral oxygen saturation (SpO2). Heart rate is derived from
//   the AC component of the PPG waveform (peak-to-peak interval detection).
//
// RESPONSIBILITIES:
//   1. Initialize the sensor over I2C (set LED currents, sample rate,
//      pulse width, and operating mode — SpO2 mode for dual-LED operation)
//   2. Read raw RED and IR ADC values from the sensor's FIFO buffer
//   3. Apply a basic DC removal filter (high-pass) to isolate the AC PPG
//      component from the baseline drift
//   4. Detect peaks in the IR waveform to compute inter-beat intervals (IBI)
//      and derive instantaneous heart rate in BPM
//   5. Compute SpO2 using the ratio-of-ratios (R-value) method:
//      R = (AC_red / DC_red) / (AC_ir / DC_ir)
//      SpO2 is then looked up from a calibration curve (linear or polynomial
//      approximation stored in a lookup table)
//   6. Expose getSpO2() and getHeartRate() methods that return the latest
//      validated readings
//
// SIGNAL QUALITY:
//   - If the sensor detects finger/probe removal (IR ADC drops below a
//     minimum threshold), readings are marked as INVALID.
//   - If the variance of SpO2 readings over a short window exceeds a
//     configured threshold (indicating motion artifact), the reading is
//     flagged for the Kalman filter to handle or discard.
//   - A simple moving average (window of 4 samples) smooths transient
//     noise without introducing significant latency.
//
// HARDWARE NOTES:
//   - I2C address: 0x57 (MAX30100) or 0x57 (MAX30102)
//   - Interrupt pin: optional — used to signal FIFO-almost-full for
//     efficient polling instead of continuous I2C reads
//   - LED current: configurable from 0 to 50 mA per LED; higher current
//     improves signal but drains battery faster. Default: 20 mA for both.
//   - Sample rate: 100 Hz is sufficient for clinical SpO2 accuracy.
//
// CALIBRATION:
//   The R-to-SpO2 lookup table is derived from standard medical device
//   calibration curves. For a prototype, a linear approximation
//   (SpO2 = 110 - 25 * R) is adequate. For production, a polynomial fit
//   against a reference pulse oximeter is required.
// =============================================================================
