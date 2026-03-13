// =============================================================================
// AyushBot Sensor Pack — TinyML Inference Engine
// =============================================================================
//
// PURPOSE:
//   This file implements the TinyML inference engine that runs the danger-sign
//   classifier on the Arduino microcontroller. It is the most safety-critical
//   code in the entire AyushBot system — a wrong prediction here could mean
//   a missed medical emergency.
//
// RESPONSIBILITIES:
//   1. Allocate the TFLite Micro tensor arena (a fixed block of SRAM used
//      by the interpreter for input/output tensors and intermediate buffers).
//      Budget: ~4-8 KB of the 256 KB available RAM.
//   2. Load the model from the byte array in model.h into the interpreter
//   3. Register only the TFLite operations (ops) actually used by the model
//      (AllOpsResolver is too large; use MicroMutableOpResolver with only
//      the specific ops the Decision Tree requires — typically just
//      FULLY_CONNECTED or custom tree ops)
//   4. Provide a runInference() function that:
//      a. Accepts a 6-element input vector: [SpO2, HR, Temp, Age, ΔSpO2, ΔHR]
//      b. Quantizes the float inputs to INT8 using the model's input scale
//         and zero-point parameters
//      c. Invokes the TFLite Micro interpreter
//      d. Dequantizes the output to retrieve the danger probability (0.0–1.0)
//      e. Compares against DANGER_THRESHOLD (0.32 from config.h)
//      f. Returns a DangerResult struct containing:
//         - is_danger: boolean
//         - confidence: float (the raw model output probability)
//         - inference_time_us: microseconds taken for this inference
//
// THRESHOLD DESIGN:
//   The threshold is intentionally set LOW (0.32 instead of the typical 0.5)
//   because the cost of a False Negative (missing a real danger) far exceeds
//   the cost of a False Positive (unnecessary alarm). This was calibrated on
//   the MIMIC-IV test set to achieve >= 0.95 sensitivity.
//
// FALLBACK:
//   If the TFLite Micro interpreter fails to initialize (model corrupt,
//   insufficient arena), this module exposes a thresholdFallback() function
//   that applies hard-coded clinical rules from config.h:
//     - SpO2 < SPO2_CRITICAL_LOW → DANGER
//     - HR > HR_CRITICAL_HIGH → DANGER
//     - Temp > TEMP_HYPERPYREXIA → DANGER
//   This ensures the system is NEVER left without danger detection capability.
//
// PERFORMANCE:
//   - Inference latency: ~0.4 ms (measured on Cortex-M4 @ 64 MHz)
//   - Tensor arena: ~4 KB RAM
//   - Model binary: ~4.2 KB Flash
//   - Total power: ~18 mW per inference cycle
//
// INTERFACE:
//   - init(): Load model, allocate arena, create interpreter. Returns bool.
//   - runInference(float inputs[6]): Run the classifier. Returns DangerResult.
//   - thresholdFallback(float spo2, float hr, float temp): Rule-based backup.
//   - getModelInfo(): Return model metadata (size, arena usage, ops count).
// =============================================================================
