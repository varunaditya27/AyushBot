# =============================================================================
# AyushBot ML — Language Agent: Train Medical NER (IndicBERT)
# =============================================================================
#
# PURPOSE:
#   Fine-tunes an IndicBERT model for medical Named Entity Recognition (NER)
#   on Indic language health text. This model is used by Agent 5 to extract
#   clinical entities (symptoms, body parts, durations) from the ASHA's input.
#
# BASE MODEL:
#   Same IndicBERT variant as the intent classifier, but with a token
#   classification head instead of sequence classification.
#
# NER ENTITY TYPES:
#   - SYMPTOM: "bukhar" (fever), "khansi" (cough), "dast" (diarrhea)
#   - BODY_PART: "chhati" (chest), "pet" (stomach), "sar" (head)
#   - DURATION: "teen din se" (for three days), "kal se" (since yesterday)
#   - SEVERITY: "bahut tez" (very high), "thoda" (a little)
#   - MEDICATION: "paracetamol", "ORS"
#
# TRAINING DATA:
#   - IHQID health query dataset with NER annotations
#   - Custom-annotated corpus of ASHA worker conversations (if available)
#   - Data augmentation via:
#     - Entity substitution (swap symptoms across examples)
#     - Back-translation (Hindi → English → Hindi for paraphrase diversity)
#     - Code-mixing augmentation (mix Hindi and English within sentences)
#
# ANNOTATION FORMAT:
#   BIO tagging scheme (Begin-Inside-Outside):
#     "bachche ko tez bukhar hai teen din se"
#     O       O  B-SEV I-SYMPTOM O B-DUR I-DUR I-DUR
#
# TRAINING PROCEDURE:
#   - Token classification head on IndicBERT
#   - Learning rate: 3e-5 (with linear warmup)
#   - Epochs: 10-15
#   - Batch size: 16
#   - Evaluation: Entity-level F1 (strict and relaxed matching)
#   - Loss: Cross-entropy with class weights (SYMPTOM entities are weighted
#     higher because they're the most critical for downstream reasoning)
#
# OUTPUT:
#   - Fine-tuned model: ml/language/models/indicbert_ner/
#   - Evaluation report: ml/language/models/ner_eval_report.json
#   - Entity distribution analysis: entity type frequencies per language
# =============================================================================
