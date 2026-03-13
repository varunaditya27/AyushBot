# =============================================================================
# AyushBot ML — Language Agent: Evaluate Indic Language Models
# =============================================================================
#
# PURPOSE:
#   Comprehensive evaluation of all language models used by Agent 5,
#   including intent classification, NER, and machine translation quality
#   across all supported Indian languages.
#
# EVALUATION COMPONENTS:
#
#   1. Intent Classification Evaluation
#      - Per-language accuracy and F1 (Hindi, Bengali, Tamil, Telugu, etc.)
#      - Cross-lingual transfer: How well does a Hindi-trained model work
#        on Bengali or Tamil queries? (IndicBERT's multilingual capability)
#      - EMERGENCY intent recall per language (must be >= 98% for ALL languages)
#      - Confusion matrix analysis: Which intents are commonly confused?
#
#   2. NER Evaluation
#      - Entity-level F1 with strict and relaxed matching per language
#      - Strict: Exact entity boundary match required
#      - Relaxed: Partial overlap counts as correct
#      - Per-entity-type performance (SYMPTOM, BODY_PART, DURATION, etc.)
#      - Error analysis: Common extraction failures (e.g., code-mixed entities)
#
#   3. Translation Quality (IndicTrans2)
#      - BLEU score on a held-out medical translation test set
#      - ChrF++ score (character-level, better for morphologically rich languages)
#      - Clinical accuracy: Do translated medical terms map correctly to
#        the clinical synonym dictionary?
#      - Bidirectional evaluation: L1→English and English→L1
#      - Human evaluation (small sample): Do translated instructions make
#        sense to native speakers? (requires manual annotation)
#
#   4. End-to-End Pipeline Test
#      Given a voice input in a local language, measure:
#        - Intent correctly classified?
#        - All clinical entities extracted?
#        - Translated symptoms map to correct English medical terms?
#        - Translated output is natural and accurate in the local language?
#        - TTS audio is intelligible?
#
# OUTPUT:
#   - Per-language evaluation matrix: ml/language/eval/language_eval_matrix.csv
#   - Cross-lingual transfer analysis report
#   - Translation quality report per language pair
#   - Identified gaps and languages needing more training data
# =============================================================================
