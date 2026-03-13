# AyushBot Data Directory
# =======================
#
# This directory holds all datasets, processed features, and corpus files
# used for training ML models and building the RAG knowledge base.
#
# IMPORTANT: Raw datasets are NOT committed to Git (too large, and some
# have restricted licenses). Only placeholder .gitkeep files and README
# documentation are committed. Researchers must download the raw data
# separately and place it here.
#
# STRUCTURE:
#
#   data/
#   ├── raw/                  → Downloaded raw datasets (git-ignored)
#   │   ├── mimiciv/          → MIMIC-IV tables (PhysioNet credentialed access)
#   │   ├── nfhs5/            → NFHS-5 survey data (DHS Program download)
#   │   ├── physionet_wearable/ → PhysioNet wearable sensor validation data
#   │   └── ihqid/            → Indian Health Query Intent Dataset
#   │
#   ├── processed/            → Pipeline outputs (git-ignored, reproducible)
#   │   ├── *.parquet         → Feature tables from ml/triage_classifier/
#   │   └── *.json            → Metadata, class weights, statistics
#   │
#   ├── corpus/               → RAG knowledge base source material
#   │   ├── raw_pdfs/         → Downloaded ASHA guideline PDFs (git-ignored)
#   │   ├── cleaned_text/     → Extracted + cleaned text (gitignored)
#   │   └── chunks/           → Chunked text (output of rag/pipeline/chunker.py)
#   │
#   └── synthetic/            → Synthetic data for testing and augmentation
#       └── health_gym/       → Synthetically generated patient records
#
# DATA LICENSES & ACCESS:
#   - MIMIC-IV: PhysioNet Credentialed Access (CITI training + DUA required)
#   - NFHS-5: Open access from DHS Program / IIPS
#   - PhysioNet Wearable: PhysioNet Open Access
#   - IHQID: Research license (cite original paper)
#   - ASHA Guidelines: Government of India public documents (NHM)
