# =============================================================================
# AyushBot ML — Triage Classifier: Step 6 — ONNX Export & Quantization
# =============================================================================
#
# PURPOSE:
#   Exports the trained XGBoost model to ONNX format and optionally quantizes
#   it for optimized inference on the Raspberry Pi 4 gateway. ONNX Runtime
#   provides hardware-optimized inference that can be faster than XGBoost's
#   native predict() for production serving.
#
# EXPORT PIPELINE:
#
#   1. Convert XGBoost model to ONNX using onnxmltools:
#        - Input: XGBoost JSON model from Step 4
#        - Output: ONNX graph with TreeEnsembleClassifier operator
#        - Verify: Run the ONNX model on the test set and confirm outputs
#          match the original XGBoost model (max absolute difference < 1e-6)
#
#   2. Apply ONNX Runtime Quantization (optional):
#        - Dynamic quantization: weights quantized to INT8, activations
#          computed in FP32 at runtime
#        - Reduces model size by ~4x with minimal accuracy impact
#        - On RPi 4: typically yields 1.5-2x speedup for tree models
#
#   3. Benchmark inference latency:
#        - Run 1000 inference iterations on the test set
#        - Report: mean latency (ms), p50, p95, p99
#        - Target: < 5 ms per inference on RPi 4 ARM64
#
#   4. Package for deployment:
#        - Copy the ONNX model to a deployment-ready directory
#        - Generate a model card JSON with: model name, version, accuracy,
#          latency, input schema, output schema, training data description
#
# OUTPUTS:
#   - ml/triage_classifier/model/xgb_triage.onnx (float model)
#   - ml/triage_classifier/model/xgb_triage_quantized.onnx (INT8 model)
#   - ml/triage_classifier/model/onnx_benchmark.json (latency results)
#   - ml/triage_classifier/model/model_card.json
#
# CLI: python -m ml.triage_classifier.06_export_onnx
# =============================================================================
