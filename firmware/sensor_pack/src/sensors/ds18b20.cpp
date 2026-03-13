// =============================================================================
// AyushBot Sensor Pack — DS18B20 Digital Temperature Sensor Driver
// =============================================================================
//
// PURPOSE:
//   Hardware abstraction layer for the DS18B20 waterproof digital temperature
//   probe. This driver handles the OneWire protocol communication, temperature
//   conversion, and reading of the final Celsius value.
//
// WHAT THE DS18B20 DOES:
//   The DS18B20 is a 1-Wire digital thermometer that provides 9-to-12-bit
//   Celsius temperature measurements. It communicates over a single data wire
//   (plus ground), making it ideal for compact sensor packs. It measures
//   temperature in the range -55°C to +125°C with ±0.5°C accuracy in the
//   clinically relevant range (0°C to 70°C).
//
// RESPONSIBILITIES:
//   1. Initialize the OneWire bus on the configured data pin
//   2. Detect the DS18B20 device address on the bus (supports single device)
//   3. Issue a temperature conversion command (takes up to 750 ms at 12-bit
//      resolution — during this time the MCU can perform other tasks)
//   4. Read the raw 16-bit temperature value from the sensor's scratchpad
//   5. Convert raw bytes to degrees Celsius (with fractional precision)
//   6. Expose getTemperature() method returning the latest reading in °C
//
// CLINICAL CONTEXT:
//   - Normal body temperature: 36.1°C to 37.2°C
//   - Fever threshold (config.h): >= 38.0°C
//   - Hypothermia threshold (config.h): <= 35.0°C (critical for neonates)
//   - Hyperpyrexia (medical emergency): >= 41.5°C
//   These thresholds are used by the TinyML classifier and the threshold-
//   based fallback alarm in main.cpp.
//
// MEASUREMENT NOTES:
//   - The waterproof probe variant is used for axillary (armpit) measurement,
//     which is the standard method for ASHA workers with children.
//   - Axillary readings are typically 0.5-1.0°C lower than core temperature;
//     this offset is applied in config.h as an adjustment factor.
//   - Resolution is set to 12-bit (0.0625°C precision) by default. Can be
//     reduced to 9-bit for faster conversion (94 ms) if speed is critical.
//
// ERROR HANDLING:
//   - If no device is found on the OneWire bus, initialization returns false
//     and main.cpp continues without temperature data (graceful degradation).
//   - If a CRC check on the scratchpad data fails, the reading is discarded
//     and the previous valid reading is retained.
// =============================================================================
