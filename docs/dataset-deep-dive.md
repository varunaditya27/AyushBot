# Dataset Deep Dive: AyushBot ASHA Co-Pilot Pipeline
## Complete End-to-End Analysis of Every Dataset and Knowledge Source

---

## Overview: The Dataset Ecosystem

The pipeline draws from four distinct data categories, each serving a different functional layer of the system. Understanding which dataset feeds which component — and exactly why — is critical for both project execution and paper credibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATASET → PIPELINE MAPPING                           │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ DATASET / SOURCE              │ PIPELINE COMPONENT IT FEEDS                 │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ MIMIC-IV                      │ Triage classifier pre-training               │
│                               │ Vital-sign normalizer training               │
│                               │ Differential diagnosis model pre-training    │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ NFHS-5                        │ FL node initialization (district priors)     │
│                               │ India-context fine-tuning of triage model    │
│                               │ Ground-truth disease prevalence validation   │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ Health Gym (Synthetic)        │ Rare-condition augmentation                  │
│                               │ Reinforcement learning for referral agent    │
│                               │ Safe training without any CITI requirement   │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ IHQID                         │ Language agent: query intent classification  │
│                               │ Multilingual entity extraction from ASHA     │
│                               │ voice/text input                             │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ PhysioNet Wearables           │ Sensor pipeline validation (SpO2, HR, temp)  │
│ (ScientISST MOVE,             │ Signal quality filter training               │
│  BIG IDEAs, Stress Dataset)   │ Motion artifact correction                   │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ RAG Corpus                    │ EdgeRAG knowledge index                      │
│ (MoHFW STWs, WHO IMCI,        │ Differential diagnosis knowledge retrieval   │
│  NHM ASHA Modules,            │ Referral criteria retrieval                  │
│  NCAP-CH, BIS/WHO water)      │ Drug dosage lookup                           │
│                               │ Water-safety advisory retrieval              │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

---

## Dataset 1: MIMIC-IV (Medical Information Mart for Intensive Care IV)

### What It Is

MIMIC-IV is the world's largest publicly accessible de-identified electronic health record database. Published by MIT's Laboratory for Computational Physiology and sourced from Beth Israel Deaconess Medical Center (BIDMC) in Boston, it captures over a **decade of clinical care data (2008–2022)** for patients admitted to the emergency department and ICU. The dataset was published in *Scientific Data* (Nature) in 2023 and has been cited hundreds of times in AI/health research.

**Scale:**
- **299,712 patients** (v3.0, October 2024)
- **431,231 hospital admissions**
- **73,181 ICU stays**
- Over **5.84 million FHIR-standard resources** in the interoperable version

### Modular Structure

MIMIC-IV is organized into five modules, each independently accessible:

| Module | Tables | Key Contents |
|---|---|---|
| **hosp** (Hospital) | 31 tables | Demographics, diagnoses (ICD-9/10), lab events, prescriptions, procedures, microbiology |
| **icu** | 6 tables | High-frequency vital signs (charted at 1–5 min intervals), ventilator settings, fluid balance |
| **ed** | 7 tables | Emergency department triage, vital signs on arrival, disposition |
| **note** | Clinical notes | Discharge summaries, radiology reports, nursing notes (requires separate credentialing) |
| **cxr** | Chest X-ray images | 377,110 de-identified radiographs linked to clinical records |
| **ecg** | 10-second 12-lead ECGs | 800,000+ diagnostic ECGs |
| **waveform** | High-resolution waveforms | PPG, ECG at bedside frequency |

### Key Variables (Most Relevant to AyushBot)

**From `icu/chartevents`** (the single most used table — ~330 million rows):
- Heart Rate (item ID 220045)
- SpO2 / Pulse Oximetry (item ID 220277)
- Respiratory Rate (item ID 220210)
- Temperature Celsius (item ID 223762)
- Systolic BP (item ID 220179), Diastolic BP (item ID 220180)
- GCS Eye/Verbal/Motor (consciousness scoring)

**From `hosp/diagnoses_icd`:**
- Primary and secondary diagnoses using ICD-9 and ICD-10 codes
- 262 disease categories with >1,000 instances each

**From `hosp/prescriptions`:**
- Drug name, dose, route, frequency — useful for the drug-dosage lookup component

**From `hosp/admissions`:**
- Admission type, discharge disposition, length of stay, in-hospital mortality flag

### How MIMIC-IV Fits the AyushBot Pipeline

**Step 1: Triage Classifier Pre-Training**

The triage classifier is the core ML model in Agent 1 (Intake & Pre-Triage). Its job is: given a set of vital signs, predict risk level (Low / Medium / High / Critical).

From MIMIC-IV, you extract:
- **Input features:** Heart rate, SpO2, temperature, respiratory rate, GCS score at ICU admission
- **Labels:** In-hospital mortality, ICU length of stay > 3 days, need for ventilation — these serve as proxy labels for "High/Critical" risk
- **Extraction query:** Select all `chartevents` records within the first 2 hours of ICU admission, join with `admissions` for outcome labels

The result is a labeled dataset of ~70,000+ ICU admissions with vital-sign features and risk outcomes. You train a lightweight model (decision tree, XGBoost, or a small MLP) on this — it serves as the pre-trained base before India-specific fine-tuning.

**Step 2: Differential Diagnosis Training Signal**

From `diagnoses_icd`, you can build a mapping: {vital sign patterns} → {most common ICD-10 diagnoses}. This trains the differential diagnosis agent's prior — i.e., given SpO2 < 88% and HR > 130, what are the most likely diagnosis categories in the training data? This is the signal that the RAG retrieval queries are conditioned on.

**Step 3: Drug Dosage Lookup Validation**

The `prescriptions` table gives real drug-dose-route associations, which can validate the RAG-retrieved drug dosage guidance from MoHFW STWs. If the RAG returns "Amoxicillin 250mg oral TDS for child pneumonia", the MIMIC-IV prescription data for similar diagnoses serves as a cross-validation anchor.

### The Transfer Learning Gap — and How You Address It

MIMIC-IV is US ICU data. ASHA workers serve primary care in rural India. The conditions are different, the severity distribution is different, and the patient demographics are different. This is not a showstopper — it is a **documented research contribution**:

1. **Use MIMIC-IV for pre-training only** (learning general vital-sign → risk mappings).
2. **Fine-tune on NFHS-5 derived data** (described in Dataset 2) for India-specific calibration.
3. **Document the transfer gap** in the paper as a limitation and show that fine-tuning closes it — this is a standard and publishable experimental design.

Published work (METRE, 2023) already shows that models trained on MIMIC-IV and evaluated on eICU (a different institution) have AUC change as small as ±0.019, demonstrating strong transferability even across institutions — let alone when fine-tuning is applied.

### Access & Practical Steps

1. Complete the CITI "Data or Specimens Only Research" online course — takes approximately 2 hours.
2. Register on PhysioNet (physionet.org), link CITI certificate.
3. Submit a data use agreement (DUA) — typically approved within 1–3 business days.
4. Download via Python using the `physionet-client` library or via wget.
5. Recommended access pattern: use the pre-processed MIMIC-IV Extract pipeline (Python) to get a clean patient × feature matrix without writing complex SQL from scratch.

**Storage requirements:** Full MIMIC-IV is ~7GB compressed. The `icu` module alone (most relevant) is ~2GB. You don't need the full dataset — a curated cohort of 10,000–50,000 patients is sufficient for training the triage classifier.

---

## Dataset 2: NFHS-5 (National Family Health Survey — Wave 5, 2019–21)

### What It Is

NFHS-5 is the most comprehensive nationally representative health survey ever conducted in India. Executed by the International Institute for Population Sciences (IIPS) under MoHFW, it surveyed **636,699 households, 724,115 women aged 15–49, and 101,839 men aged 15–54** across all 36 states/UTs and 707 districts of India between 2019 and 2021.

It is the **ground truth for India's primary care disease and health burden** — the exact population that ASHA workers serve.

### Coverage and Variables

NFHS-5 introduced several new variables not in previous waves:

**Child Health (0–5 years) — Most ASHA-relevant:**
- Weight-for-age Z-score (SAM/MAM classification — directly maps to HX711 weight module)
- Height-for-age Z-score (stunting)
- MUAC (mid-upper arm circumference)
- Haemoglobin levels (anaemia severity classification: <7, 7–9.9, 10–10.9, 11+ g/dL)
- Diarrhea in past 2 weeks (prevalence by district)
- ARI (Acute Respiratory Infection) / fever in past 2 weeks
- ORS use during diarrhea episode
- Treatment-seeking behavior (% taken to health facility)

**Maternal Health:**
- ANC visit coverage and timing
- Institutional delivery rates by district
- Postnatal care within 2 days
- Tetanus toxoid vaccination coverage

**ASHA Interaction Data:**
- Percentage of women who received postnatal care from an ASHA
- ASHA-facilitated institutional deliveries
- ASHA-provided iron/folic acid supplements

**New in NFHS-5:**
- Blood pressure and blood glucose measurements (for adults 15+)
- Waist and hip circumference
- Disability assessment
- Death registration status

### The 707-District Dataset: The FL Initialization Gold Mine

The district-level breakdown of NFHS-5 is what makes it uniquely valuable for the federated learning design of AyushBot.

Each FL node in the simulation corresponds to a distinct disease-burden profile. NFHS-5 gives you **real, district-level heterogeneity data** to initialize these nodes:

- Kerala districts: low child malnutrition, high blood pressure, better treatment-seeking
- Rajasthan/UP districts: high SAM prevalence, high ARI, low institutional delivery
- Odisha/Jharkhand: higher malaria burden, higher anemia
- Maharashtra urban vs rural: stark contrast in ASHA contact rates

You randomly partition NFHS-5 districts into 5–10 FL node groups, each reflecting a realistic regional disease mix. This is what makes your FL simulation **grounded in real heterogeneity** — not a synthetic split — and is a direct contribution to the paper.

**A 2025 Nature Scientific Reports paper has already demonstrated ML on NFHS-5**, using supervised ML to predict community health worker impact on delivery outcomes — validating that the dataset is ready for ML pipelines.

### How NFHS-5 Fits the Pipeline

**1. India-Context Fine-Tuning:**
Extract a derived feature matrix from NFHS-5:
- Child: age_months, weight_for_age_z, haemoglobin_g_dl, diarrhea_2wk_flag, ari_2wk_flag
- Outcome labels: severe_acute_malnutrition (yes/no), severe_anaemia (yes/no), treatment_sought (yes/no)

Fine-tune the MIMIC-IV pre-trained triage classifier on this India-specific feature-label pairs. The model learns: "In Indian primary care, a child with Hb < 7 + low weight-for-age = Critical; a child with mild fever + no respiratory symptoms = Low."

**2. Disease Prior Distribution per FL Node:**
For each simulated FL node (district cluster), compute:
- P(diarrhea | under-5 child)
- P(ARI | under-5 child)
- P(SAM | under-5 child, rural)

These become the Bayesian prior probabilities used by Agent 2 (Differential Diagnosis) when the RAG retrieves candidate conditions. They are also the initialization parameters for each FL node's local model.

**3. Ground-Truth Validation:**
After training, validate referral decisions against NFHS-5 treatment-seeking behavior: "Does the model recommend referral for the same case profiles where NFHS-5 shows families actually sought formal care?" This is a real-world behavioral validation of the referral agent.

### Access & Format

- Download from **dhsprogram.com** (DHS Program, USAID)
- Data available as: Flat ASCII, SPSS (.sav), Stata (.dta), SAS transport
- Python readable using `pyreadstat` or `pandas` with pre-processing
- IIPS India also provides summary Excel files by district — useful for node initialization without downloading the full flat files
- **No individual-level approval needed** for district-level aggregate files
- Individual-level microdata requires a free registration on the DHS Program website (same-day approval for academic research)

**Storage:** Full household + individual recode files ~2GB compressed.

---

## Dataset 3: Health Gym (Synthetic Clinical Datasets)

### What It Is

Health Gym is an open-source platform developed by researchers at UNSW Sydney, the George Institute for Global Health, and Imperial College London, funded by Wellcome Trust. It generates **highly realistic synthetic patient datasets** using Generative Adversarial Networks (GANs) trained on real clinical databases (primarily MIMIC-III/IV).

Published in *Nature Scientific Data* (2022) and *JMIR Medical Education* (2024), Health Gym is designed specifically for ML research prototyping and education — no CITI training, no DUA, no access barriers.

The identity disclosure risk for Health Gym datasets was estimated at **0.045%** — essentially zero, making them safe for open use and sharing within your team.

### Available Datasets

**1. Synthetic Sepsis Dataset (PhysioNet hosted)**
- Generated from MIMIC-III sepsis cohort
- Features: 48 hours of ICU vitals, labs, interventions
- Variables: HR, MAP, temperature, GCS, creatinine, lactate, vasopressor use, fluid balance
- 5,000 synthetic patient trajectories
- **Pipeline use:** Augment MIMIC-IV training data with sepsis-like high-acuity cases; test the triage classifier's ability to identify severe systemic infection

**2. Synthetic Acute Hypotension Dataset (PhysioNet hosted)**
- Generated from MIMIC-III hypotension cohort
- Variables: blood pressure, vasopressor dose, fluid input/output
- **Pipeline use:** Train the triage classifier's shock/hypotension recognition; validate SpO2 + HR + BP feature interactions

**3. Synthetic HIV/ART Dataset (FigShare hosted)**
- Generated from real ART patient data
- Variables: CD4 count, viral load, antiretroviral drug regimen
- **Pipeline use:** Secondary use — extends the co-pilot's capability to HIV patients (relevant for India's rural burden); demonstrates multi-disease generalizability in the paper

### Why Health Gym Matters for AyushBot Beyond Just Augmentation

**Problem:** The MIMIC-IV + NFHS-5 combination gives you good coverage of common Indian primary care conditions (SAM, anaemia, ARI) but rare or acute conditions (septic shock, severe hypotension, severe malaria complication) will be underrepresented in your training data.

**Solution:** Health Gym fills this gap by providing:
1. **Rare-condition training examples** without any privacy or access concern
2. **Counterfactual patient trajectories** — the GAN generates "what would happen if this patient received different interventions?" — useful for the referral agent's decision modeling
3. **Team-shareable training data** — since there's no DUA, your full team can work with it simultaneously without individual credentialing

**Reinforcement Learning for the Referral Agent:**
Health Gym was specifically designed for **offline reinforcement learning** — the referral agent can be framed as an RL problem: given a patient state, choose an action (home management / PHC referral / emergency referral) to maximize a reward (correct referral → positive outcome). The Health Gym RL environment gives you a ready-to-use training framework for this.

### Access

- Sepsis and Hypotension datasets: **physionet.org/content/synthetic-mimic-iii-health-gym/** — no credentialing needed
- HIV/ART dataset: **figshare.com** — open access
- GitHub: **github.com/NicKuo-ResearchStuff/Health_Gym_AI** — full preprocessing pipelines and worked examples
- Format: CSV files with patient × timestep × feature structure

---

## Dataset 4: IHQID (Indian Healthcare Query Intent Datasets)

### What It Is

IHQID (Indian Healthcare Query Intent Dataset) consists of two datasets — **IHQID-WebMD** and **IHQID-1mg** — published at EACL 2023 (Findings of the Association for Computational Linguistics, one of the top NLP venues). Created by researchers from IIT Kharagpur, it is the **only publicly available multilingual healthcare intent and entity dataset for Indian languages**.

The datasets were created by:
1. Crawling frequently asked questions from WebMD India and 1mg (India's largest online pharmacy)
2. Collecting real-world healthcare queries from doctors at Indian hospitals
3. Annotating with intent labels and named entity categories
4. Translating and validating across seven languages

### Coverage

**Languages:** English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati (7 total)

**Intent Classes:**
- Symptom description ("I have chest pain and difficulty breathing")
- Drug query ("What is the dose of ORS for a 2-year-old?")
- Disease information ("What are signs of malaria?")
- Treatment query ("How to treat watery diarrhea at home?")
- Referral need ("When should I take the child to hospital?")
- Diagnostic query ("Why would SpO2 be low?")

**Entity Categories:**
- Disease names (e.g., "pneumonia", "malaria")
- Drug names (e.g., "Amoxicillin", "Cotrimoxazole")
- Symptoms (e.g., "fast breathing", "pallor", "fever")
- Body parts
- Dosages and frequencies

**Scale:**
- IHQID-WebMD: Hundreds of queries per language per intent class
- IHQID-1mg: Similar scale with pharmacy/drug focus
- Real-world hospital test set: 100 queries per language

### How IHQID Fits the Pipeline

**Agent 5: Language & Accessibility Agent**

ASHA workers will interact with the co-pilot in their local language — typing or speaking in Kannada, Hindi, Tamil, Marathi, or Telugu. The Language Agent must:
1. Identify the **intent** of the query (symptom report? drug question? referral decision?)
2. Extract **named entities** (disease names, symptoms, drug names) from the local-language input
3. Map them to standardized medical terms for the downstream agents

IHQID directly trains and evaluates this pipeline. The ACL 2023 paper provides baseline F1 scores for XLM-RoBERTa and mBERT on these tasks — you use these as your baseline comparison and attempt to beat them using a fine-tuned IndicBERT or AI4Bharat model.

**Practical pipeline:**
```
ASHA speaks in Kannada:
"ಮಗುವಿಗೆ 3 ದಿನದಿಂದ ಭೇದಿ ಇದೆ, ತೂಕ ಕಡಿಮೆ ಇದೆ"
("Child has had diarrhea for 3 days, low weight")
        ↓ Language Agent: Intent = Symptom Report
        ↓ Entity Extraction: disease=diarrhea, duration=3days, finding=low_weight
        ↓ Mapped to: {condition_candidate: ["acute gastroenteritis", "SAM"], vitals_needed: ["weight", "temperature"]}
        ↓ Passed to Agent 1 (Intake & Pre-Triage)
```

**Access:** ACL Anthology (aclanthology.org) — open access paper with dataset link. GitHub repository linked from the paper.

---

## Dataset 5: PhysioNet Wearable Biosignal Datasets

### Why a Dedicated Wearable Dataset Category?

The MAX30100/30102 sensor on the Arduino is a real-world device operating in non-clinical conditions — the ASHA is holding it to the patient's finger during a home visit. In clinical settings, pulse oximetry is well-controlled. In field conditions, signal quality degrades from:
- **Motion artifact** (patient moving)
- **Poor perfusion** (cold hands, anemia reducing pulse amplitude)
- **Ambient light interference** (bright sunlight)
- **Sensor placement errors** (ASHA not holding it correctly)

A signal quality filter and motion artifact correction model must be trained on real wearable PPG data with these characteristics — not clean ICU monitor data from MIMIC-IV.

### Three Specifically Relevant PhysioNet Datasets

**1. ScientISST MOVE (Multimodal Wearable Biosignals)**
- **Signals:** ECG, EMG, EDA, PPG, Temperature, Accelerometer (ACC) — all simultaneous
- **Device:** ScientISST Sense + Empatica E4 (wrist-worn wearables)
- **Activities:** Everyday life activities in naturalistic environments (sitting, walking, typing, etc.)
- **Why it matters:** PPG signal quality during movement = exactly the motion artifact scenario ASHAs face. The ACC signal lets you train a motion artifact correction model: "When ACC shows high movement AND PPG signal shows low amplitude, flag HR reading as unreliable."
- **Pipeline use:** Train signal quality classifier and motion artifact filter for the Arduino MAX30100 readings

**2. BIG IDEAs Lab Glycemic Variability and Wearable Dataset**
- **Signals:** Continuous glucose monitoring + wrist-worn wearable data (HR, EDA, Temperature, BVP, ACC)
- **Participants:** High-normoglycemic participants
- **Why it matters:** Provides wrist-worn Temperature and HR data under free-living conditions — the closest analog to what an ASHA's sensor pack will produce
- **Pipeline use:** Validate that the temperature + HR feature fusion for triage is meaningful in wearable (vs clinical) signal quality conditions

**3. Wearable Device Dataset from Induced Stress and Structured Exercise**
- **Device:** Empatica E4 wristband
- **Signals:** PPG/BVP (64 Hz), 3-axis Accelerometer (32 Hz), Infrared Thermopile (4 Hz), EDA (4 Hz)
- **Participants:** 36 healthy volunteers during structured stress induction and aerobic/anaerobic exercise
- **Why it matters:** High-HR conditions during exercise mimic elevated HR in fever and infection — the Empatica E4 PPG under stress tests whether HR estimation remains accurate when the patient is physically distressed
- **Pipeline use:** Train and validate the HR estimation algorithm's robustness at clinically relevant elevated heart rate ranges (80–160 bpm)

### How These Fit the Sensor Pipeline Specifically

```
RAW MAX30100 SIGNAL
        ↓
Signal Quality Classifier (trained on ScientISST MOVE ACC + PPG)
        ↓ "Acceptable quality" → proceed
        ↓ "Motion artifact" → prompt ASHA to re-measure
        ↓
HR Estimation Algorithm (trained + validated on BIG IDEAs + Stress datasets)
        ↓
Temperature Correction (ambient vs body temperature differential model)
        ↓
CLEAN VITALS OUTPUT → Agent 1 (Intake & Pre-Triage)
```

**Access:** All three are on PhysioNet (physionet.org). The ScientISST MOVE and BIG IDEAs datasets are open-access (no credentialing needed). The Stress dataset requires standard PhysioNet registration.

---

## Dataset 6: The RAG Corpus — Clinical Knowledge Documents

### Structure and Purpose

The RAG corpus is not a "dataset" in the statistical ML sense — it is a **curated collection of authoritative clinical documents** that gets chunked, embedded, and indexed into the EdgeRAG knowledge store. Its quality is the most direct determinant of whether the differential diagnosis and referral agents give correct, safe, and actionable outputs.

### Document-by-Document Analysis

**Document 1: ASHA Training Modules 1–7 (NHM India)**
- *Source:* nhm.gov.in / nhsrcindia.org
- *Content:* 7 progressive training modules covering ASHA duties, community health education, reproductive & child health, disease surveillance, and skill building. Module 6 & 7 cover clinical skills in most depth.
- *Format:* PDF (Hindi + English versions available)
- *RAG use:* Chunks about specific disease management procedures and referral criteria are the highest-retrieval-frequency items — this is what the ASHA co-pilot will query most.
- *Critical note:* The ASHA Induction Module (NHM 2021) is freely downloadable from nhsrcindia.org. The full Module 6 & 7 PDFs are available on nhm.gov.in.

**Document 2: Standard Treatment Workflows (MoHFW)**
- *Source:* mohfw.gov.in
- *Content:* Clinical protocols for 100+ conditions covering diagnosis criteria, first-line treatment, drug dosages, referral criteria. Organized by disease category.
- *Format:* PDF (English)
- *RAG use:* Primary source for the Referral Planning Agent — the referral criteria sections are chunked and indexed with high priority. Drug dosage tables are extracted as structured JSON and stored separately for faster lookup.
- *Critical note:* Not all STWs are uniformly accessible in one document. The MoHFW website hosts them by disease category. You will need to download ~10–15 PDF documents, consolidate, and clean them. Estimated effort: 4–6 hours of corpus preparation.

**Document 3: WHO IMCI Guidelines (Integrated Management of Childhood Illness)**
- *Source:* who.int — openly available as a full-color illustrated manual
- *Content:* The global gold standard for under-5 child health triage at the primary care level. The IMCI "danger signs" classification system (General Danger Signs → immediate referral) is the clinical backbone of the triage agent's rule set.
- *Format:* PDF (available in 6 UN languages)
- *RAG use:* The IMCI "assess and classify" flowcharts are the most important content — chunks containing "classify as" and "treat as" keywords are retrieved most frequently by the Differential Diagnosis Agent.
- *Critical note:* The WHO IMCI pocket book (2013 edition, updated 2024) is freely downloadable and is 380 pages of high-density clinical information. This single document is worth more than any other in the corpus.

**Document 4: National List of Essential Medicines India (NLEM)**
- *Source:* mohfw.gov.in (2022 edition)
- *Content:* 384 medicines available at various levels of the health system, with formulations, dosage forms, and indications. Organized by therapeutic category.
- *Format:* PDF + Excel
- *RAG use:* The referral agent queries this to confirm: "Is the recommended drug available at PHC level?" If not, it adjusts the recommendation or flags the supply gap. Also used by the drug dosage lookup component.

**Document 5: India NCAP-CH (National Action Plan on Climate Change & Human Health)**
- *Source:* ncdc.mohfw.gov.in
- *Content:* India's official health response to climate change. Covers climate-sensitive disease protocols (heat stroke, vector-borne disease, waterborne illness), early warning systems, and community health worker roles in climate-health response.
- *Format:* PDF (2021 edition)
- *RAG use:* Feeds the secondary SDG 13 component. When the ASHA's location or season flag suggests climate-linked disease risk (monsoon + diarrhea, heatwave + fever), the RAG retrieves from NCAP-CH to add a climate-health context to the advisory.

**Document 6: BIS IS:10500 / WHO Water Quality Guidelines**
- *Source:* BIS summary publicly available; WHO GDWQ (2022 edition) at who.int
- *Content:* Drinking water quality standards — permissible limits for turbidity, TDS, coliform, pH, chemical contaminants. WHO GDWQ adds health-risk context for contaminant exceedances.
- *Format:* PDF
- *RAG use:* When an ASHA reports "family uses well water" and child has diarrhea, the water-safety advisory retrieval queries this document. Output: "Well water turbidity above IS:10500 limit of 1 NTU is associated with elevated diarrheal risk; recommend boiling or chlorination."

### RAG Corpus Construction Pipeline

```
RAW PDFs (MoHFW, NHM, WHO, BIS)
        ↓ PDF extraction (PyPDF2 or pdfminer)
        ↓ Text cleaning (remove headers, footers, page numbers, figure captions)
        ↓ Section-aware chunking (500–800 token chunks with 50-token overlap)
        ↓ Medical term normalization (disease name → ICD-10 code mapping)
        ↓ Embedding generation (sentence-transformers: all-MiniLM-L6-v2 or BioLORD)
        ↓ K-means clustering (EdgeRAG compression step)
        ↓ Centroid-indexed vector store (FAISS or ChromaDB, then exported to flat file)
        ↓ DEPLOYED ON RPi 4 AS LOCAL .faiss INDEX FILE
```

**Estimated corpus stats:**
- Total pages: ~500–700 across all documents
- Cleaned text tokens: ~600,000–900,000
- Chunks (at 600 tokens): ~1,000–1,500 chunks
- Embedding dimensionality: 384 (MiniLM-L6-v2) or 768 (BioLORD)
- Final compressed EdgeRAG index size: ~50–80 MB — easily fits on RPi 4's SD card

---

## Synthetic Data Generation Strategy (Where Gaps Exist)

Despite strong coverage, there are specific gaps where synthetic generation is necessary and methodologically defensible:

### Gap 1: India-Specific Vital Sign Distributions by Condition

MIMIC-IV gives vital-sign distributions for ICU patients in the US. NFHS-5 gives prevalence but not detailed vital signs. For specific Indian primary care conditions (severe dengue, cerebral malaria, severe SAM with complications), the vital-sign distributions need to be synthesized from published Indian clinical studies.

**Method:**
1. Extract mean ± SD for HR, SpO2, temperature, and weight-for-age from published Indian journal papers (IJPM, Indian Pediatrics, Indian Journal of Medical Research — all open access).
2. Generate N=1,000–5,000 synthetic patients per condition using multivariate Gaussian sampling with inter-feature correlations from MIMIC-IV.
3. Calibrate: verify that generated distributions match published Indian clinical case series statistics.

**Precedent:** This approach is standard in global health AI research and is explicitly validated in Health Gym's GAN-based generation methodology.

### Gap 2: ASHA Interaction Simulation Data

No dataset captures an ASHA's actual clinical decision-making dialog. You generate this synthetically:

1. Define 20–30 patient case profiles (age, sex, vitals, symptoms, NFHS-5 derived condition) — these are your test cases.
2. For each, generate the "ground truth" action from WHO IMCI (the paper-checklist gold standard).
3. These become evaluation examples: run AyushBot on each case, compare its recommendation to IMCI gold standard, compute accuracy.

---

## Cross-Validation Summary: Feasibility Scorecard

| Dataset | Coverage of Pipeline Need | Access Complexity | Data Quality | India Relevance |
|---|---|---|---|---|
| **MIMIC-IV** | Pre-training, vital-sign modeling, drug validation | Low (2-hr CITI + DUA, 1–3 days) | ⭐⭐⭐⭐⭐ (MIT-published, 10+ years) | Medium (US ICU → transfer required) |
| **NFHS-5** | India fine-tuning, FL initialization, validation | Very Low (free DHS registration, same day) | ⭐⭐⭐⭐⭐ (govt survey, 636k households) | ⭐⭐⭐⭐⭐ (India-specific, district-level) |
| **Health Gym** | Rare-condition augmentation, RL training | Zero (fully open, no approval) | ⭐⭐⭐⭐ (GAN-generated, identity risk 0.045%) | Medium (US-origin synthetic, augmentation role) |
| **IHQID** | Language agent training, Indic NLU | Zero (ACL open access) | ⭐⭐⭐⭐ (ACL 2023 peer-reviewed) | ⭐⭐⭐⭐⭐ (India-specific, 7 Indic languages) |
| **PhysioNet Wearables** | Sensor pipeline validation | Very Low (PhysioNet registration) | ⭐⭐⭐⭐ (annotated, validated devices) | Medium (wearable signal quality universally applicable) |
| **RAG Corpus (PDFs)** | Knowledge base, retrieval quality | Zero (all public PDFs) | ⭐⭐⭐⭐⭐ (WHO/MoHFW authoritative) | ⭐⭐⭐⭐⭐ (India-specific clinical guidelines) |

---

## Full Data Flow: How All Datasets Connect in One View

```
                        ┌──────────────────────┐
                        │  MIMIC-IV (pre-train) │
                        └──────────┬───────────┘
                                   │ base triage model weights
                        ┌──────────▼───────────┐
                        │  NFHS-5 (fine-tune)   │
                        └──────────┬───────────┘
                                   │ India-calibrated triage model
                ┌──────────────────▼──────────────────┐
                │         FL NODE INITIALIZATION       │
                │  Node 1: Kerala priors (NFHS-5)      │
                │  Node 2: UP/Bihar priors (NFHS-5)    │
                │  Node 3: Odisha priors (NFHS-5)      │
                └──────────────────┬──────────────────┘
                                   │ FL training rounds
                        ┌──────────▼───────────┐
                        │  Health Gym (augment) │───► RL reward shaping for
                        └──────────────────────┘      referral agent
                                   │
                    ┌──────────────▼──────────────┐
                    │    TRIAGE + DIFF DX AGENT    │
                    │ (trained model, ready)       │
                    └──────────────┬──────────────┘
                                   │
         ┌─────────────────────────▼──────────────────────────┐
         │              EdgeRAG INDEX (RPi 4)                   │
         │  MoHFW STWs + WHO IMCI + NLEM + NCAP-CH + BIS water │
         └─────────────────────────┬──────────────────────────┘
                                   │ retrieved passages
                    ┌──────────────▼──────────────┐
                    │  DIFFERENTIAL DIAGNOSIS +    │
                    │  REFERRAL PLANNING AGENTS    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   LANGUAGE AGENT             │
                    │ (IHQID-trained intent +      │
                    │  entity model)               │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ SENSOR PIPELINE (MAX30100)   │
                    │ Signal quality filter:       │
                    │ ScientISST MOVE + BIG IDEAs  │
                    └──────────────────────────────┘
```
