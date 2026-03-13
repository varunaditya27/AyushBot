# =============================================================================
# AyushBot ML — Language Agent: Train Intent Classifier (IndicBERT)
# =============================================================================
#
# PURPOSE:
#   Fine-tunes an IndicBERT model for clinical intent classification on
#   Indic language health queries. This model is used by Agent 5 (Language
#   Agent) to classify the ASHA worker's input into one of the clinical
#   intent categories.
#
# BASE MODEL:
#   ai4bharat/IndicBERTv2-MLM-Sam-TLM (or similar IndicBERT variant)
#   - Pre-trained on 23 Indian languages
#   - ~110M parameters
#   - Handles code-mixing (Hindi-English, Bengali-English, etc.)
#
# TRAINING DATA:
#   - IHQID (Indian Health Query Intent Dataset): Primary training source
#   - Augmented with synthetic health queries generated from clinical
#     templates in multiple Indian languages
#   - Example queries and intents:
#     "bachche ko tez bukhar hai" (Hindi) → SYMPTOM_REPORT
#     "SpO2 88 matlab kya hai?" (Hindi) → VITAL_QUERY
#     "kitna paracetamol dena hai?" (Hindi) → DRUG_QUERY
#     "baccha saans nahi le raha" (Hindi) → EMERGENCY
#     "vaccination kab hai?" (Hindi) → GENERAL
#
# INTENT CLASSES:
#   - SYMPTOM_REPORT: ASHA describing patient symptoms
#   - VITAL_QUERY: Asking about vital sign meaning
#   - DRUG_QUERY: Asking about medication dosage
#   - EMERGENCY: Reporting a critical/life-threatening situation
#   - GENERAL: Health information queries (vaccination, nutrition, etc.)
#
# TRAINING PROCEDURE:
#   - Sequence classification head on top of IndicBERT [CLS] token
#   - Learning rate: 2e-5 (with warmup)
#   - Epochs: 5-10
#   - Batch size: 16
#   - Evaluation: 5-fold cross-validation
#   - Metrics: Accuracy, macro-F1, per-class F1
#   - EMERGENCY class recall MUST be >= 98% (never miss an emergency)
#
# OUTPUT:
#   - Fine-tuned model: ml/language/models/indicbert_intent/
#   - Evaluation report: ml/language/models/intent_eval_report.json
# =============================================================================
