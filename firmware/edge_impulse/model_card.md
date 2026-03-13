# TinyML Danger-Sign Classifier — Model Card

## Purpose

This model card documents the TinyML danger-sign classifier deployed on the
Arduino Nano 33 BLE Sense as part of the AyushBot sensor pack. It follows
the Model Card standard for transparent ML model documentation.

## Model Details

- **Model type:** Quantized Decision Tree (max depth 5)
- **Framework:** TensorFlow Lite Micro (or Edge Impulse export)
- **Quantization:** INT8 fixed-point (lossless for tree splits)
- **Binary size:** ~4.2 KB
- **Input features:** 6 — SpO2, HR, Temperature, Age (months), ΔSpO2 (30s), ΔHR (30s)
- **Output:** Binary classification (DANGER / SAFE) with confidence score
- **Classification threshold:** 0.32 (optimized for high recall / sensitivity)

## Training Data

- **Source:** PhysioNet MIMIC-IV v3.0, `icu/chartevents` table
- **Cohort:** 70,341 complete ICU admissions with 2-hour vital sign records
- **Labels:** DANGER = in-hospital mortality OR ICU stay > 5 days
- **Class balance:** SMOTE applied to achieve 1:2 positive-to-negative ratio
- **Split:** 70% train / 15% validation / 15% test (stratified)

## Performance Metrics

These fields will be populated after training is complete:

- **AUC:** (target: >= 0.92)
- **Sensitivity at threshold 0.32:** (target: >= 0.95)
- **Specificity:** (target: >= 0.85)
- **Inference latency on Arduino Nano 33 BLE:** (target: < 1 ms)
- **RAM usage:** (target: < 8 KB tensor arena)
- **Flash usage:** (target: < 5 KB model binary)
- **Power consumption:** (target: < 20 mW per inference)
- **Battery life at continuous monitoring:** (target: >= 11 hours)

## Intended Use

- **Primary:** Hardware-level fail-safe danger detection for ASHA health workers
  conducting household visits in rural India.
- **Not intended for:** Standalone clinical diagnosis. This model only flags
  potential emergencies for further assessment by the multi-agent system
  (Agents 1-3) and the ASHA worker. It is a safety net, not a diagnostic tool.

## Limitations

- Trained on US ICU data (MIMIC-IV), not Indian primary-care data. Performance
  on Indian patient populations requires validation and FL-based fine-tuning.
- Only considers 6 vital sign features. Does not account for symptom history,
  medication, or comorbidities (those are handled by Agent 1 on the gateway).
- Decision tree may underperform on complex non-linear decision boundaries
  compared to neural networks, but this trade-off is accepted for determinism,
  auditability, and INT8 quantization compatibility.

## Ethical Considerations

- The threshold is deliberately set low (0.32) to minimize false negatives
  at the cost of higher false positives. A false alarm is inconvenient;
  a missed emergency is potentially fatal.
- The model does not use race, ethnicity, or socioeconomic status as features.
- All training data is de-identified and accessed under PhysioNet DUA.
