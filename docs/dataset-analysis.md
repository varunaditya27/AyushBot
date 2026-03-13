# AyushBot Dataset Deep Analysis: End-to-End Feasibility Report

## Dataset Architecture Overview

The AyushBot pipeline has **three distinct data needs**, and each must be satisfied differently:

| Need | What it feeds | Dataset type |
|---|---|---|
| **Training the ML triage classifier** | Intake Agent + FL nodes | Structured clinical EHR + vitals data |
| **Training the NLU/language module** | Language & Accessibility Agent | Annotated healthcare query data in Indic languages |
| **Building the EdgeRAG knowledge index** | Differential Diagnosis + Referral Agents | Curated clinical documents (PDFs → text chunks → embeddings) |
| **Sensor pipeline validation** | Sensor Pack signal quality | Wearable biosignal recordings |
| **Augmenting rare and India-specific cases** | All model fine-tuning | Synthetic generation frameworks |

No single dataset covers all needs. The strategy is **stratified multi-source dataset assembly**, which is standard in clinical AI research. Each dataset below is analyzed along six dimensions: what it is, its structure and scale, access process, what pipeline component it feeds, how it is used specifically, and what its limitations are (and how you mitigate them).

---

## Dataset 1: MIMIC-IV (Medical Information Mart for Intensive Care, Version 3.0)

### What It Is

MIMIC-IV is the largest freely accessible de-identified EHR dataset in the world, maintained by MIT's Laboratory for Computational Physiology and hosted on PhysioNet. It contains over a decade of in-patient clinical records from Beth Israel Deaconess Medical Center (BIDMC), a tertiary care hospital in Boston, USA. It is the gold standard benchmark dataset for clinical machine learning research globally.

### Structure and Scale

MIMIC-IV v3.0 (released late 2024) contains:
- **364,627 unique patients** across 546,028 hospitalizations and 94,458 ICU stays
- Two primary modules:
  - **`hosp` module:** Hospital-wide EHR data — diagnoses (ICD-9/10), lab events, prescriptions, procedures, in-hospital outcomes, admissions/discharge metadata
  - **`icu` module:** High-frequency time-series from MetaVision — charted vitals (HR, SpO2, BP, RR, Temp), interventions, fluid outputs, minute-to-minute sensor streams
- **Key tables for this project:**
  - `chartevents`: >300 million rows of time-stamped ICU vital sign measurements — SpO2, heart rate, temperature, respiratory rate, blood pressure
  - `diagnoses_icd`: ICD-coded diagnoses per hospital admission — maps conditions to patient encounters
  - `labevents`: >120 million rows of lab results (hemoglobin for anemia detection, WBC for infection, etc.)
  - `admissions`: demographic info, admission type, discharge status, time of death if applicable
  - `patients`: age, gender, date of birth — basic demographic features

MIMIC-IV also has a **FHIR-formatted version** (mimic.mit.edu/fhir) with 315,000 patients and 5.84 million resources in NDJSON format, which is more directly usable in a FHIR-compatible pipeline.

### Access Process

1. Complete the **CITI Program "Data or Specimens Only Research" course** (free, ~2 hours online)
2. Create a PhysioNet account and submit the course completion certificate
3. Sign the PhysioNet data use agreement
4. Access is typically granted **within 24–72 hours**
5. Data is downloaded from physionet.org/content/mimiciv/ — full download is ~35 GB; filtered subsets are much smaller

### How It Feeds the Pipeline: Specific Usage

**Primary use — pre-training the triage risk classifier (Intake Agent):**
- Extract cohorts of patients with high-burden primary-care conditions relevant to ASHA's scope: respiratory illness (ICD J06, J18, J22), severe anemia (ICD D50–D64), diarrheal disease (ICD A00–A09), fever/sepsis (ICD A41), malnutrition (ICD E40–E46), pregnancy-related complications (ICD O codes)
- For each patient, extract the **first 6 hours of ICU/ED vitals** (SpO2, HR, Temp, RR) as the input feature vector — this mimics what an ASHA's sensor pack would measure
- Label each case with the primary discharge diagnosis and severity (ICU admission = high severity; ward discharge = medium; ED discharge = low)
- Train a gradient boosted classifier or lightweight neural network: Input = [SpO2, HR, Temp, weight-for-age Z-score, age, gender] → Output = [Low / Medium / High / Critical risk, most likely condition cluster]

**Secondary use — RAG corpus validation:**
- Use MIMIC-IV's clinical notes module (MIMIC-IV-Note) to extract language patterns from clinician documentation of the same conditions
- This enriches the RAG query formulation with realistic clinical language

**Benchmark use — evaluating the Differential Diagnosis Agent:**
- Use known ICD-coded cases as a gold standard: given the first-hour vitals, does the differential diagnosis agent rank the correct condition first? This is a measurable, publishable evaluation metric.

### Limitations and Mitigations

| Limitation | Severity | Mitigation |
|---|---|---|
| US ICU data, not Indian primary-care | High | Use MIMIC for pre-training only; fine-tune on NFHS-5 and synthesized Indian-context data |
| ICU patients are sicker than ASHA-visited patients | Medium | Filter for lower-severity admissions (ED discharge, short-stay); subsample to match ASHA-relevant condition distribution |
| English clinical notes only | Low (notes not used for the core triage task) | Language Agent handles translation separately |
| No pediatric malnutrition Z-scores | Medium | Augment with NFHS-5 anthropometric data; use WHO growth standards |

---

## Dataset 2: NFHS-5 — National Family Health Survey 2019–21 (India)

### What It Is

NFHS-5 is India's most comprehensive nationally-representative health and demographic survey, conducted by the International Institute for Population Sciences (IIPS), Mumbai, under the Ministry of Health and Family Welfare (MoHFW). Wave 5 (2019–21) is the latest available round.

### Structure and Scale

- **636,699 households** surveyed across all states/UTs and 707 districts
- **Sample composition:** Women aged 15–49, men aged 15–54, children under 5, and household-level data
- **Key modules for this project:**
  - **Child health and nutrition:** weight-for-age Z-scores (WAZ), height-for-age Z-scores (HAZ), MUAC measurements, hemoglobin levels, vaccination status, diarrhea and ARI (acute respiratory infection) incidence in past 2 weeks
  - **Maternal health:** antenatal care visits, institutional delivery, postnatal care, skilled birth attendance — all core ASHA duties
  - **CHW contact data:** Was the household visited by an ASHA? What services were rendered? This is uniquely valuable — it lets you model the ASHA-patient interaction itself
  - **District-level estimates:** 707-district-level health indicators published separately — usable to initialize FL node priors per district
  - **Blood biomarkers:** Hemoglobin (anemia screening), blood glucose (diabetes), blood pressure (hypertension) — measured for sampled adults/children
- **Data formats:** Household, Women, Men, and Child recode datasets in SPSS/Stata/flat file formats. Conversion to CSV is trivial.

### Access Process

- Go to **dhsprogram.com**, register as a researcher (free, ~5 minutes), and submit a brief project description
- Data access is typically granted **same day or within 48 hours**
- The NFHS-5 factsheets are also available directly on **aikosh.indiaai.gov.in** under Open Government License without any registration
- Raw individual-level data requires DHS Program registration; aggregate district factsheets are fully open

### How It Feeds the Pipeline: Specific Usage

**Primary use — India-context fine-tuning of the triage classifier:**
- Use child health records with hemoglobin + weight-for-age + diarrhea/ARI occurrence to create an Indian-context training set
- Labels: children with hemoglobin < 8 g/dL = severe anemia; WAZ < -3 = severe acute malnutrition; ARI in past 2 weeks + age < 5 = pneumonia risk flag
- Fine-tune the MIMIC-IV pre-trained classifier on this subset → the model learns Indian-specific distribution (smaller stature norms, higher anemia prevalence, tropical disease patterns)

**Critical use — Federated Learning node initialization:**
- Partition NFHS-5 by district → each partition becomes the initialization dataset for one simulated FL node
- Districts like Malda (West Bengal, high anemia), Korba (Chhattisgarh, high malaria), Bellary (Karnataka, high malnutrition) have distinct disease profiles
- Simulating 5–10 FL nodes from different districts demonstrates that FL captures local disease heterogeneity — the paper's key FL contribution (RQ3)

**Validation use — ASHA-contact effect modeling:**
- A 2025 Nature Scientific Reports paper has already applied supervised ML to NFHS-5 CHW-contact data to predict institutional delivery outcomes — proving this dataset is ML-ready and that ASHA-contact is a predictive feature
- Use the same approach to validate: do patients in ASHA-visited households have better documented health outcomes? This grounds the project's "why ASHA tools matter" claim with data

### Limitations and Mitigations

| Limitation | Severity | Mitigation |
|---|---|---|
| Survey data, not clinical records — no longitudinal follow-up | Medium | Use as distribution reference and fine-tuning data, not as outcome prediction data |
| Self-reported disease incidence (2-week recall) | Medium | Supplement with IDSP laboratory-confirmed case data for validation |
| No individual SpO2 or vital sign measurements | High | Use hemoglobin + symptom flags as proxies; generate synthetic vitals using MIMIC-IV distribution statistics conditioned on diagnosis |
| 2019–21 data — may miss COVID-era and post-COVID changes | Low | Disease burden patterns for TB, anemia, malnutrition, maternal conditions are structurally stable |

---

## Dataset 3: Health Gym — Synthetic Clinical Datasets

### What It Is

Health Gym is an open-source platform (University of New South Wales, Australia, in collaboration with Imperial College London and The George Institute for Global Health) that generates **highly realistic synthetic medical datasets** using Generative Adversarial Networks (GANs) trained on MIMIC-III. Published in *Scientific Data* (Nature) and with a 2024 JMIR Medical Education follow-up paper validating its use in education and prototyping.

### Structure and Scale

Three core datasets currently available:
1. **Sepsis dataset:** ~19,000 synthetic ICU patient trajectories with hourly vital signs, lab values, and treatment decisions — modeled on the MIMIC-III sepsis cohort. Features: MAP, SpO2, HR, lactate, WBC, antibiotic administration.
2. **Acute Hypotension dataset:** ~10,000 synthetic patients, modeled on MIMIC-III vasopressor cohort. Features: HR, MAP, fluid inputs, vasopressor doses.
3. **ART for HIV dataset:** ~10,000 synthetic patient trajectories with longitudinal CD4 count, viral load, and antiretroviral therapy decisions.

Each dataset is provided as time-series CSV files. The GAN architecture (Wasserstein GAN with gradient penalty) ensures **extremely low re-identification risk (estimated at 0.045%)** while preserving statistical fidelity to the original data.

### Access Process

- Fully open-source and freely downloadable from GitHub: **github.com/Nic5472K/ScientificData2021_HealthGym**
- No registration, no approval, no data use agreement
- Preprocessing code, tutorials, and Jupyter notebooks are included

### How It Feeds the Pipeline: Specific Usage

**Primary use — augmenting rare and severe cases in the training set:**
- The triage classifier needs examples of severe conditions (sepsis, severe respiratory failure) that may be rare in NFHS-5 but critical to correctly flag
- The Health Gym sepsis dataset provides synthetic examples of deteriorating vital-sign trajectories (falling SpO2, rising HR, dropping BP) that train the classifier to recognize the critical risk level
- Use the sepsis dataset to generate "synthetic ASHA home visit equivalents" for critically ill patients — take the first 2 vital sign timepoints from Health Gym trajectories as if they were ASHA sensor readings

**Secondary use — validating the EdgeRAG retrieval on complex cases:**
- Generate edge-case query scenarios (e.g., "Patient with MAP 60, SpO2 85%, HR 130, temperature 40.2°C — what's the diagnosis and referral?") using Health Gym trajectories
- These synthetic cases allow systematic stress-testing of the differential diagnosis agent on high-severity presentations without ethical concerns about using real patient data

**Tertiary use — RL-based future extension:**
- Health Gym was designed specifically for reinforcement learning in clinical settings — the project can propose a future direction where the triage agent is improved via offline RL on Health Gym trajectories

### Limitations and Mitigations

| Limitation | Severity | Mitigation |
|---|---|---|
| US ICU-derived; same domain gap as MIMIC | Medium | Same mitigation as MIMIC-IV: use for augmentation, not primary training |
| Only sepsis, hypotension, HIV — no malnutrition/anemia datasets | Medium | Use the Health Gym GAN framework to generate India-calibrated synthetic data from NFHS-5 statistics |
| Synthetic data may not capture all real-world correlations | Low | Validated to preserve statistical fidelity at 0.045% re-identification risk; supplement with NFHS-5 |

---

## Dataset 4: IHQID — Indian Healthcare Query Intent Dataset (ACL/EACL 2023)

### What It Is

IHQID is a gold-standard, peer-reviewed NLP dataset for healthcare query understanding in Indian languages, proposed by researchers from IIT Kharagpur and published at EACL 2023 (Findings of the Association for Computational Linguistics). It is the **only annotated multilingual healthcare query dataset for India** and is precisely what the Language & Accessibility Agent requires.

### Structure and Scale

Two sub-datasets:
- **IHQID-WebMD:** Healthcare queries scraped and translated from WebMD India, annotated for intent and entities. Covers English, Hindi, Bengali, Tamil, Telugu, Marathi, and Gujarati
- **IHQID-1mg:** Queries from 1mg (India's largest digital pharmacy), annotated similarly — more grounded in Indian health-seeking behavior (self-medication, drug queries, symptom lookup)
- **Real-world hospital dataset:** Actual queries from Indian hospital information desks — anonymized, multilingual, annotated

**Annotations per query:**
- **Intent labels:** Symptom inquiry, Disease information, Drug/medication query, Appointment/referral, Emergency, General wellness
- **Entity labels:** Body part, Disease name, Drug name, Symptom, Duration, Severity

### Access Process

- Available through **ACL Anthology** (aclanthology.org/2023.findings-eacl.140) — open access
- Dataset download link provided in the paper; also available via **Papers with Code** (paperswithcode.com)
- No registration required

### How It Feeds the Pipeline: Specific Usage

**Primary use — training the Language Agent's intent classifier:**
- Train a multilingual intent classifier (using IndicBERT or mBERT as backbone) on IHQID to understand what the ASHA is asking
- Example: ASHA says in Hindi: "इस बच्चे को बुखार और सांस लेने में दिक्कत है" (This child has fever and difficulty breathing) → Intent: Symptom inquiry → Entities: [fever, respiratory distress, child] → Route to Differential Diagnosis Agent

**Secondary use — grounding the RAG query formulation:**
- The knowledge agent needs to formulate retrieval queries in English from Indic-language symptom descriptions
- IHQID entity labels map to standardized medical terms → these normalized terms are used as RAG retrieval queries
- Example: "सांस लेने में दिक्कत" → [respiratory distress] → RAG query: "IMCI danger signs fast breathing tachypnea management"

**Evaluation use:**
- Evaluate the Language Agent's intent classification accuracy on the IHQID test split → a concrete, publishable metric for the paper's language component

### Limitations and Mitigations

| Limitation | Severity | Mitigation |
|---|---|---|
| Queries from WebMD/1mg — patient queries, not health worker queries | Medium | Fine-tune on a small manually annotated ASHA-specific query set (20–50 examples per category is sufficient for few-shot adaptation) |
| Gujarati included but not all south Indian languages (Kannada missing) | Low | IndicBERT's pre-training covers Kannada; IHQID fine-tuning transfers via multilingual representations |
| No audio/speech component | Medium | Use AI4Bharat ASR model for voice-to-text before IHQID-based intent classification |

---

## Dataset 5: PhysioNet Wearable Biosignal Datasets

### 5A. ScientISST MOVE (PhysioNet 2024)

**What it is:** A multimodal wearable biosignal dataset recorded during natural everyday activities, developed by ScientISST (Instituto Superior Técnico, Portugal). Published on PhysioNet in March 2024.

**Structure:**
- 17 healthy volunteers (10 male, 7 female), median age 24
- Biosignal modalities: **ECG, EMG (bicep), EDA (electrodermal activity), PPG (photoplethysmography), TEMP (wrist temperature), ACC (accelerometry)** — 7 modalities
- Devices: 2x ScientISST Core + 1x Empatica E4 wristband
- Body locations: chest, abdomen, left bicep, wrist, index finger
- Activities: lifting, greeting, gesticulating, walking, running, jumping
- ~37 minutes of synchronized data per subject
- Sampling rates: ECG at 1000 Hz, PPG at 100 Hz, temperature at 4 Hz
- Format: European Data Format (EDF); also on Zenodo

**How it feeds the pipeline:**
- The PPG channel directly corresponds to what the MAX30100 sensor outputs — train the signal quality assessment module on ScientISST MOVE PPG recordings to learn which motion artifacts corrupt SpO2 and HR readings
- The TEMP channel validates the DS18B20 temperature reading pipeline
- EDA (galvanic skin response) can be used for a secondary stress/anxiety proxy, extending the system's scope
- Realistic test cases: run the trained sensor pipeline on ScientISST walking/running segments to test artifact rejection

**Access:** PhysioNet standard credentialing (same as MIMIC-IV); also freely available on Zenodo without any registration

---

### 5B. Pulse Transit Time PPG Dataset (PhysioNet)

**What it is:** A dataset from 22 healthy subjects with multi-site, multi-wavelength PPG recordings, synchronized ECG, blood pressure, and accelerometry. Includes SpO2 at start and end of each measurement period using both a clinical blood pressure monitor and an iHealth pulse oximeter (similar to MAX30100 class devices).

**How it feeds the pipeline:**
- Provides a paired (sensor reading ↔ reference SpO2) dataset for calibrating the MAX30100 sensor module in the ASHA sensor pack
- Trains a bias-correction model: given MAX30100 raw output, predict the true SpO2 more accurately
- 19 channels of synchronized data allow feature extraction beyond SpO2 — heart rate variability (HRV) features that may improve the triage classifier's sensitivity

---

### 5C. BIG IDEAs Lab Glycemic Variability and Wearable Device Data

**What it is:** A PhysioNet dataset from the University of Pittsburgh BIG IDEAs Lab containing glucose measurements paired with wrist-worn wearable sensor data. Included because a significant fraction of ASHA's adult patients have undiagnosed or unmanaged diabetes.

**How it feeds the pipeline:**
- Provides a template for extending the sensor pack to include a non-invasive glucose proxy (HRV + temperature correlates with glycemic state in the literature)
- Useful for demonstrating the extensibility of the sensor pipeline beyond the core 3 sensors

**Access for all PhysioNet datasets:** Same CITI credentialing as MIMIC-IV — one registration gives access to all PhysioNet databases.

---

## Dataset 6: The RAG Corpus — Clinical Knowledge Documents

This is not a single dataset but a curated collection of authoritative documents that form the EdgeRAG knowledge index. Unlike the ML datasets above, these are not used for model training — they are chunked, embedded, and indexed for retrieval.

### 6A. MoHFW Standard Treatment Workflows (STWs)

**What they are:**
India's ICMR, National Health Authority, and WHO India office jointly developed Standard Treatment Workflows — a set of visual, evidence-based clinical decision flowcharts for India's healthcare system. As of 2024, STWs cover 100+ conditions across:
- Paediatric conditions (TB, malnutrition, ARI, diarrhea, neonatal care)
- Maternal health (antenatal care, postpartum hemorrhage, eclampsia)
- Vector-borne diseases (dengue, malaria, chikungunya)
- Skin diseases (13 modules published 2024)
- NCD conditions (diabetes, hypertension, heart failure)
- Mental health conditions

They are designed specifically for use at PHC/CHC level — the exact care tier at which ASHAs operate and refer to.

**Access:** Freely downloadable as PDFs from mohfw.gov.in, clinicalestablishments.mohfw.gov.in, and icmr.gov.in. Physical posters are also placed in health centers.

**How it feeds the RAG pipeline:**
- PDFs are parsed using a document processing library (PyPDF2 or Camelot for tables)
- Text is chunked at the section level (each flowchart step becomes a chunk)
- Chunks are embedded using a small multilingual embedding model (e.g., sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — runs efficiently on RPi 4)
- Chunks are stored in the EdgeRAG clustered vector index
- Example retrieval: Query = "SpO2 88%, fast breathing in 14-month child" → Top-3 retrieved chunks = [IMCI danger sign: fast breathing, STW Paediatric Respiratory, STW Referral criteria to CHC]

---

### 6B. NHM ASHA Training Modules (Induction + Modules 1–7)

**What they are:** The National Health Mission's official ASHA training curriculum — 7 modules plus an Induction Module covering the full scope of ASHA duties: maternal health, child health, nutrition, family planning, vector control, water/sanitation, mental health. Available in English and all major Indian languages.

**Key content sections for RAG:**
- Section 5: Common diseases — malaria, diarrhea, ARI, fever — with field-level management guidance
- Section 6: Maternal health — ANC schedule, warning signs, institutional delivery facilitation
- Section 7: Child nutrition — MUAC classification, severe acute malnutrition (SAM) protocols
- Drug list: Which medicines ASHAs are authorized to dispense (ORS, iron-folic acid, co-trimoxazole, etc.)

**Access:** Directly downloadable as PDFs from nhm.gov.in (confirmed available). Urban ASHA module also available at nhm.gov.in/NUHM.

**Why this is the most critical RAG document:** The Differential Diagnosis Agent should speak the language of ASHA training — using the same terminology, the same referral criteria thresholds, and the same drug names that ASHAs have been trained on. This ensures the co-pilot reinforces existing knowledge rather than contradicting it.

---

### 6C. WHO IMCI Guidelines (Integrated Management of Childhood Illness)

**What it is:** WHO's gold-standard framework for managing childhood illness in resource-limited settings — the most evidence-based and field-validated paediatric triage protocol globally. The IMCI chart booklet uses simple clinical signs (fast breathing, chest indrawing, inability to drink, convulsions, stridor) to classify severity and determine management.

**How it feeds the RAG pipeline:**
- The IMCI danger sign classification thresholds (e.g., RR > 50/min for fast breathing in infants, > 40/min in children) are extracted and stored as high-priority retrieval chunks
- The Intake Agent's rule-based pre-filter is initialized from IMCI thresholds
- The Differential Diagnosis Agent's output is evaluated against IMCI classifications in the paper's evaluation

---

### 6D. India National Action Plan on Climate Change & Human Health (NCAP-CH)

**What it is:** Developed by NCDC under MoHFW (2024 update), this plan covers climate-linked disease surveillance, heat action plans, vector control, and waterborne disease prevention specific to India.

**How it feeds the RAG pipeline:**
- For climate-linked queries (heat stroke risk, post-monsoon diarrhea risk, dengue season), the RAG retriever pulls from NCAP-CH sections
- This is what enables AyushBot to address SDG 13 — the co-pilot can answer: "It's peak heatwave season and this patient is confused with high temperature — what do I do?" and retrieve the heat action protocol

---

### 6E. BIS IS:10500 Drinking Water Standards + WHO Water Quality Summary

**What it feeds:**
- SDG 6 component of the RAG corpus
- Enables queries like "The household uses borewell water. Child has diarrhea. Is there a water risk?" → retrieves BIS permissible limits and advises on water treatment/testing

---

## Dataset 7: IDSP — Integrated Disease Surveillance Programme (India)

### What It Is

The IDSP is India's national disease surveillance network under MoHFW/NCDC, covering all districts. It collects **weekly disease surveillance data** from health workers (S form — suspected), clinicians (P form — presumptive), and lab staff (L form — confirmed). Currently, ~97% of districts report weekly.

### Data Available

- Weekly district-level counts of suspected, presumptive, and confirmed cases for epidemic-prone diseases: dengue, malaria, cholera, typhoid, acute diarrheal disease, acute respiratory illness, viral hepatitis, encephalitis
- **Outbreak reports:** Detailed line-list data for outbreak investigations — available on the IDSP portal (idsp.mohfw.gov.in) and published as outbreak investigation reports
- Historical outbreak data going back to 2008 in some categories

### Access

- Aggregate state/district-level data: publicly accessible on the IDSP portal without login
- Detailed line-list outbreak data: requires a request to IDSP/NCDC; typically available to researchers with institutional affiliation
- Published outbreak reports: freely downloadable PDFs from the IDSP portal

### How It Feeds the Pipeline

**Population-level disease prior calibration:**
- IDSP weekly district data gives the **current disease incidence rate** for dengue, malaria, acute diarrheal disease, etc. by district
- These rates initialize the prior probability weights in the Differential Diagnosis Agent
- Example: In August (peak dengue season) in a Karnataka district with 200 dengue cases/week, the agent's prior for dengue should be substantially elevated vs January in the same district
- This makes AyushBot seasonally and geographically aware — a novel and publishable feature

**FL node validation:**
- Partition IDSP data by district × disease × season to create realistic "local data distributions" for FL node simulation

---

## Dataset Assembly Strategy: Full Pipeline Map

```
                        ┌─────────────────────────────────────────────────┐
                        │          AAYUSHBOT DATASET FLOW                  │
                        └──────────────────────┬──────────────────────────┘
                                               │
          ┌──────────────────────────┬─────────┴──────────┬───────────────────┐
          ▼                          ▼                     ▼                   ▼
  ┌───────────────┐        ┌─────────────────┐   ┌──────────────────┐  ┌────────────────┐
  │ TRIAGE MODEL  │        │  EDGERAG INDEX  │   │ LANGUAGE MODULE  │  │ SENSOR PIPELINE│
  │   TRAINING    │        │  (KNOWLEDGE     │   │    (NLU + TTS)   │  │  CALIBRATION   │
  │               │        │    BASE)        │   │                  │  │                │
  └───────┬───────┘        └────────┬────────┘   └────────┬─────────┘  └───────┬────────┘
          │                         │                      │                    │
  ┌───────▼───────┐        ┌────────▼────────┐   ┌────────▼─────────┐  ┌───────▼────────┐
  │ MIMIC-IV      │        │ MoHFW STWs      │   │ IHQID-WebMD      │  │ScientISST MOVE │
  │ (pre-train)   │        │ NHM ASHA Modules│   │ IHQID-1mg        │  │PPG Transit Time│
  │ NFHS-5        │        │ WHO IMCI        │   │ Hospital Queries │  │BIG IDEAs Lab   │
  │ (fine-tune)   │        │ NCAP-CH         │   │                  │  │                │
  │ Health Gym    │        │ BIS Water Stds  │   │                  │  │                │
  │ (augment)     │        │ WHO Water Guide │   │                  │  │                │
  │ IDSP          │        │ Ess. Medicines  │   │                  │  │                │
  │ (FL priors)   │        └─────────────────┘   └──────────────────┘  └────────────────┘
  └───────────────┘
```

---

## Cross-Validation Checklist: Is the Data Really Available?

| Dataset | Confirmed Available? | Access Time | License | Student-Usable? |
|---|---|---|---|---|
| MIMIC-IV v3.0 | ✅ Yes — physionet.org | 1–3 days (CITI) | PhysioNet Credentialed Access | ✅ Yes |
| NFHS-5 raw data | ✅ Yes — dhsprogram.com | Same-day or 48h | DHS Program License (free) | ✅ Yes |
| NFHS-5 factsheets | ✅ Yes — aikosh.indiaai.gov.in | Instant | Open Government License India | ✅ Yes |
| Health Gym datasets | ✅ Yes — GitHub | Instant | Open-source (no license restrictions) | ✅ Yes |
| IHQID (WebMD + 1mg) | ✅ Yes — ACL Anthology | Instant | Research use permitted | ✅ Yes |
| ScientISST MOVE | ✅ Yes — PhysioNet + Zenodo | Instant (Zenodo) | CC BY 4.0 | ✅ Yes |
| Pulse Transit Time PPG | ✅ Yes — PhysioNet | Same as MIMIC-IV | PhysioNet Open Access | ✅ Yes |
| NHM ASHA Modules | ✅ Yes — nhm.gov.in | Instant PDF download | Government of India (open) | ✅ Yes |
| MoHFW STWs | ✅ Yes — mohfw.gov.in + icmr.gov.in | Instant PDF download | Government of India (open) | ✅ Yes |
| WHO IMCI Guidelines | ✅ Yes — who.int | Instant PDF download | WHO Permitted Reprint | ✅ Yes |
| NCAP-CH | ✅ Yes — ncdc.mohfw.gov.in | Instant PDF download | Government of India (open) | ✅ Yes |
| IDSP aggregate data | ✅ Yes — idsp.mohfw.gov.in portal | Instant web access | MoHFW open data | ✅ Yes |
| IDSP line-list data | ⚠️ Partial — aggregate public; detailed requires request | 1–2 weeks | Researcher access | Possible with institutional email |

**Result: 12 out of 13 datasets are immediately accessible without any approval bottleneck. IDSP line-list detail requires a simple email request — the aggregate public data is sufficient for the project scope.**

---

## Dataset Size vs. Compute Requirements

A common concern for student projects is whether the datasets are too large to process. Here is a practical breakdown:

| Dataset | Raw Size | Required for this project | Processing Load |
|---|---|---|---|
| MIMIC-IV | ~35 GB | ~500 MB (filtered cohort: relevant ICD codes, first-hour vitals) | Moderate; runs on Google Colab free tier |
| NFHS-5 | ~2 GB | ~200 MB (child + maternal recodes, selected variables) | Light; runs in pandas/R |
| Health Gym | ~50 MB | All 3 datasets | Trivial |
| IHQID | < 10 MB | Full dataset | Trivial |
| ScientISST MOVE | ~2 GB | ~200 MB (PPG + TEMP channels, selected subjects) | Light |
| RAG corpus (all PDFs) | ~50 MB raw | Processed text + embeddings: ~200 MB | One-time indexing: ~30 min on RPi 4 |

**Total active working dataset: approximately 1–2 GB, well within Google Drive free storage and easily manageable in Colab.**
