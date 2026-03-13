# =============================================================================
# AyushBot ML — Signal Quality: Evaluate HR/SpO2 Accuracy
# =============================================================================
#
# PURPOSE:
#   Benchmarks the accuracy of AyushBot's SpO2 and heart rate measurements
#   against a reference pulse oximeter to validate clinical acceptability.
#
# FDA/CLINICAL ACCURACY STANDARDS:
#   For SpO2 measurement accuracy:
#     - ARMS (Accuracy Root Mean Square) must be <= 3% SpO2 across the
#       70-100% range compared to a reference CO-oximeter
#     - This is the standard benchmark for medical pulse oximeters
#   For heart rate:
#     - Accuracy within ± 3 BPM compared to ECG reference
#
# EVALUATION PROTOCOL:
#
#   1. Reference Dataset
#      - Use PhysioNet wearable sensor datasets that include simultaneously
#        recorded reference pulse oximetry (e.g., from a medical-grade device)
#      - If available, collect validation data from field tests with ASHAs
#        using both AyushBot's sensor pack and a reference pulse oximeter
#
#   2. Accuracy Metrics
#      - ARMS (Accuracy Root Mean Square) for SpO2
#      - Bland-Altman analysis: plot (AyushBot reading - Reference reading) vs.
#        average of both readings
#      - Limits of Agreement (mean ± 1.96 × std of differences)
#      - Correlation coefficient (Pearson r)
#      - Mean Absolute Error (MAE) for HR
#
#   3. Condition-Stratified Analysis
#      Evaluate accuracy separately for:
#        - Normal SpO2 (>= 95%): Should be highly accurate
#        - Mild hypoxemia (90-94%): Clinically important range
#        - Severe hypoxemia (< 90%): Most critical range — accuracy here
#          determines whether Agent 1 correctly identifies CRITICAL cases
#      AND for:
#        - Clean signal (no motion artifacts)
#        - Motion-contaminated signal (after artifact filtering)
#
# OUTPUT:
#   - Bland-Altman plots: ml/signal_quality/eval/bland_altman_spo2.png
#   - ARMS values per SpO2 range
#   - HR accuracy report: ml/signal_quality/eval/hr_accuracy.json
#   - Clinical acceptability verdict: PASS/FAIL against standards
# =============================================================================
