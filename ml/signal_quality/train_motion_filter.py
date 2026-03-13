# =============================================================================
# AyushBot ML — Signal Quality: Train Motion Artifact Filter
# =============================================================================
#
# PURPOSE:
#   Trains a lightweight classifier that detects motion artifacts in PPG
#   sensor data (from the MAX30100 pulse oximeter). Motion artifacts are the
#   primary source of inaccurate SpO2/HR readings in field conditions.
#
# PROBLEM:
#   When a child moves during measurement (crying, struggling), the optical
#   PPG sensor picks up motion-induced signal variations that contaminate
#   the SpO2 and heart rate readings. Without filtering, Agent 1 would
#   receive incorrect vital signs and potentially misclassify risk.
#
# APPROACH:
#   Binary classifier on 1-second windows of raw PPG signal:
#     - Class 0: Clean signal (patient still) → reading is trustworthy
#     - Class 1: Motion artifact detected → flag reading as unreliable
#
# FEATURES (per 1-second window):
#   - Signal variance
#   - Signal kurtosis
#   - Zero-crossing rate
#   - Dominant frequency from FFT
#   - Signal-to-noise ratio estimate
#   - Accelerometer correlation (if IMU data available from Arduino)
#
# TRAINING DATA:
#   - PhysioNet wearable datasets with annotated motion artifact segments
#   - Synthetic artifacts: Add controlled noise patterns to clean PPG signals
#
# MODEL:
#   Lightweight options (must run on Arduino Nano 33 BLE or RPi 4):
#   - Random Forest (10 trees, max depth 5) — ~1 KB model
#   - Small neural network (2 layers, 8 neurons each) — ~2 KB model
#   - Decision tree (single, depth 4) — <1 KB model
#
# OUTPUT:
#   - Trained model: ml/signal_quality/models/motion_filter_model.pkl
#   - Evaluation: precision/recall on artifact detection (goal: >90% recall)
#   - Export: TFLite or decision tree C code for embedded deployment
# =============================================================================
