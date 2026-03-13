// =============================================================================
// AyushBot Sensor Pack — HX711 Load Cell Amplifier / Weight Sensor Driver
// =============================================================================
//
// PURPOSE:
//   Hardware abstraction layer for the HX711 24-bit ADC + load cell amplifier
//   module. This driver handles communication with the HX711 chip, tare
//   calibration, raw-to-kilogram conversion, and weight reading for pediatric
//   patients.
//
// WHAT THE HX711 DOES:
//   The HX711 is a precision 24-bit analog-to-digital converter designed for
//   weigh scales and industrial control. It amplifies the tiny millivolt
//   signal from a strain gauge (load cell) and provides a digital output
//   readable via a simple two-wire interface (data + clock).
//
// RESPONSIBILITIES:
//   1. Initialize the HX711 with the configured data and clock pins
//   2. Perform tare operation (zero the scale with no weight applied) —
//      this must be called at the start of each patient encounter
//   3. Read raw 24-bit ADC values from the HX711
//   4. Apply the calibration factor to convert raw ADC to weight in kilograms
//      (calibration factor is determined once per device using a known weight)
//   5. Average multiple readings (default: 10) to reduce noise
//   6. Expose getWeight() method returning weight in kilograms (float)
//   7. Expose isStable() method that returns true when consecutive readings
//      are within a small tolerance (indicating the patient is still on scale)
//
// CLINICAL CONTEXT:
//   - Weight is critical for drug dosage calculation in Agent 3 (Referral).
//     Pediatric drug doses are almost always weight-based (mg per kg).
//   - Weight-for-age Z-scores (WHO growth standards) are computed downstream
//     by Agent 1 to detect severe acute malnutrition (SAM) and moderate
//     acute malnutrition (MAM).
//   - Measurement range: 0–25 kg (covers neonates through age 5)
//   - Resolution target: ±50 grams (sufficient for clinical dosage accuracy)
//
// CALIBRATION:
//   The calibration factor must be determined per physical load cell unit.
//   The process is:
//     1. Call tare() with nothing on the scale
//     2. Place a known calibration weight (e.g., 1 kg reference weight)
//     3. Read the raw ADC value
//     4. calibration_factor = raw_value / known_weight_kg
//   This factor is stored in config.h or EEPROM for persistence across reboots.
//
// ERROR HANDLING:
//   - If the HX711 chip is not responding (data pin stays high indefinitely),
//     initialization returns false and main.cpp continues without weight data.
//   - Negative weight readings (after tare) are clamped to 0.0 kg.
//   - Readings that spike above the physical maximum (e.g., 30 kg for a
//     pediatric scale) are discarded as noise.
// =============================================================================
