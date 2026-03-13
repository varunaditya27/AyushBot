// =============================================================================
// AyushBot Sensor Pack — Multi-Sensor Kalman Filter
// =============================================================================
//
// PURPOSE:
//   Implements a lightweight Kalman filter for fusing and denoising the three
//   sensor streams (SpO2, Heart Rate, Temperature) into a single, noise-
//   minimized state estimate. This is the signal conditioning layer that sits
//   between raw sensor reads and the TinyML classifier input.
//
// WHY A KALMAN FILTER:
//   When multiple noisy sensors measure overlapping physiological phenomena
//   simultaneously, simply taking raw readings introduces noise propagation.
//   A patient who is running a fever AND has low SpO2 AND has elevated HR
//   from physical exertion (vs from sepsis) requires the system to correctly
//   interpret the multi-sensor state, not treat each reading independently.
//
//   The Kalman filter produces an optimal (minimum variance) state estimate
//   by combining the prediction from a simple physiological model with the
//   noisy measurements, weighted by their respective uncertainties.
//
// STATE VECTOR:
//   The filter maintains a state vector with the following components:
//     x = [SpO2, HR, Temperature]
//
//   Each component has an associated uncertainty (covariance) that shrinks
//   as more measurements confirm a consistent trend, and grows when
//   measurements are inconsistent or missing.
//
// PROCESS MODEL (Prediction Step):
//   - Assumes vital signs change slowly between measurement intervals
//     (constant-state model with small process noise).
//   - Process noise Q is tuned per vital sign:
//       SpO2 changes slowly (Q_spo2 = small)
//       HR can change rapidly during exertion (Q_hr = larger)
//       Temperature changes very slowly (Q_temp = smallest)
//
// MEASUREMENT MODEL (Update Step):
//   - Each sensor provides a direct (linear) measurement of one state variable.
//   - Measurement noise R is set per sensor based on datasheet specifications:
//       R_spo2 (MAX30100) = ±2% typical accuracy
//       R_hr (MAX30100) = ±3 BPM typical
//       R_temp (DS18B20) = ±0.5°C typical
//
// ADDITIONAL FEATURES:
//   - If a sensor reading is flagged as INVALID (by signal quality checks in
//     the driver), the Kalman update for that variable is skipped — the filter
//     relies on its prediction model, which gracefully coasts through brief
//     measurement gaps.
//   - An outlier rejection gate: if a new measurement deviates from the
//     predicted value by more than 3 standard deviations (Mahalanobis
//     distance), it is treated as a motion artifact and rejected.
//
// IMPLEMENTATION CONSTRAINTS:
//   - Uses fixed-point arithmetic (no floats) to run efficiently on the
//     Cortex-M4 without FPU overhead — or uses the Cortex-M4F FPU if
//     available on the Nano 33 BLE (which does have an FPU).
//   - Total RAM usage for the 3-state filter: approximately 100-200 bytes
//     (state vector + covariance matrix + temporary buffers).
//
// INTERFACE:
//   - init(): Set initial state estimates and covariance
//   - predict(): Run the prediction step (called every KALMAN_UPDATE_INTERVAL)
//   - update(sensor_id, measurement): Incorporate a new sensor reading
//   - getState(): Return the current fused state estimate [SpO2, HR, Temp]
//   - getUncertainty(): Return the diagonal of the covariance matrix
// =============================================================================
