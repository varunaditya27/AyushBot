Here is the complete, exhaustive Product Requirements Document for AyushBot.

***

# AyushBot — Product Requirements Document (PRD)
## Version 1.0 | R.V. College of Engineering, Bengaluru | March 2026

***

## Table of Contents

1. Executive Summary
2. Problem Statement & Motivation
3. Project Identity and Naming
4. Research Novelty and Contributions
5. System Architecture Overview
6. Functional Requirements by Layer
7. The Five-Agent Orchestration System
8. ML Model Pipeline Requirements
9. EdgeRAG Subsystem Requirements
10. Federated Learning Subsystem Requirements
11. IoT Hardware Requirements
12. Computer Networks Requirements
13. Algorithms Requirements
14. Discrete Mathematics Requirements
15. Dataset Requirements
16. Non-Functional Requirements
17. Security and Privacy Requirements
18. SDG Alignment
19. Evaluation and Benchmarking Framework
20. Research Publication Roadmap
21. Deployment and Field Pilot Plan
22. Risk Register
23. Glossary

***

## 1. Executive Summary

AyushBot is an offline-first, privacy-preserving, multi-agent healthcare decision-support system designed specifically for Accredited Social Health Activists (ASHAs) — India's frontline community health workers who serve 900 million rural citizens. The system integrates five cooperating autonomous AI agents, a locally-deployed Retrieval-Augmented Generation (RAG) pipeline, a privacy-preserving Federated Learning (FL) subsystem, and a low-cost Arduino-based physiological sensor pack to deliver grounded, evidence-backed, multilingual triage guidance to ASHAs during household visits — without requiring internet connectivity.

The project is simultaneously a product prototype deployable in real-world PHC (Primary Health Centre) environments and a research artifact targeting publication in top-tier international journals. It bridges four undergraduate computer science courses — Internet of Things, Computer Networks, Design and Analysis of Algorithms, and Discrete Mathematical Structures and Combinatorics — through a cohesive, deep-tech implementation that addresses a genuine, empirically documented national healthcare gap.

The system targets SDG 3 (Good Health), SDG 9 (Innovation and Infrastructure), SDG 10 (Reduced Inequalities), and SDG 4 (Quality Education through open-source curriculum integration).

***

## 2. Problem Statement and Motivation

### 2.1 The ASHA Worker Operational Reality

India's ASHA workers are the lowest-level, highest-reach health workers in the world. Each ASHA is responsible for 1,000 people in a geographic village cluster. She conducts 18 to 20 home visits per day, assessing mothers, neonates, and children for conditions including severe acute malnutrition, pneumonia, diarrhea, anemia, neonatal danger signs, and high-risk pregnancy flags. She makes referral decisions daily that determine whether a child lives or dies.

Yet she does this with no clinical decision support whatsoever. Her only tools are a paper register, a basic smartphone with a government mobile health record (MHR) application, and her training memory from modules she attended months or years ago.

### 2.2 The Three Documented Gaps

**Gap 1 — Connectivity.** Independent research in Meghalaya documented that 100% of sampled ASHA workers cited poor internet connectivity as their primary operational barrier. Cloud-based AI tools are therefore operationally infeasible as primary decision-support infrastructure in rural India.

**Gap 2 — Usability.** A 2024 systematic review identified 11 documented usability failures in ASHA documentation diaries: cognitive overload from complex navigation, poor visual hierarchy, excessive data entry, and lack of multilingual voice support. Existing tools digitize paperwork but not clinical intelligence.

**Gap 3 — Trust and Privacy.** India's Digital Personal Data Protection Act (DPDPA) 2023 imposes strict data localization requirements on health data. Centralizing patient records in cloud servers violates these requirements. ASHAs and their communities need a system that keeps patient data on-device.

### 2.3 The Research Gap

Despite significant global research activity in clinical AI, federated learning for healthcare, and edge deployment, no prior published system integrates:
- EdgeRAG deployed on commodity edge hardware (Raspberry Pi-class devices) for clinical knowledge retrieval
- Multi-agent orchestration for primary-care triage with explicit evidence citation
- Federated learning evaluated on real geographic disease heterogeneity (Indian district distributions from NFHS-5)
- TinyML hardware-level danger-sign detection as a fail-safe layer
- End-to-end multilingual support for Indian regional languages at the edge
- All of the above in a unified, deployment-ready system for community health workers

AyushBot fills this gap entirely.

***

## 3. Project Identity and Naming

**Full Name:** AyushBot: A Privacy-Preserving Federated Multi-Agent EdgeRAG Co-Pilot for Offline-First Rural Healthcare Triage in India

**Short Name:** AyushBot

**Name Rationale:** "Ayush" is derived from Ayushman Bharat, India's national health mission and digital health framework. It also carries the Sanskrit meaning of "long life" or "health." "Bot" signals the AI co-pilot nature without suggesting full autonomy — reinforcing the design philosophy that the system empowers the ASHA worker, not replaces her clinical judgment.

**Target User:** ASHA (Accredited Social Health Activist) workers operating in Tier-3 and Tier-4 Indian villages with intermittent or absent mobile internet.

**Stakeholders:**
- Primary: ASHA workers (direct daily users)
- Secondary: Medical Officers at PHCs (receive referral notes, model update triggers)
- Tertiary: State and District Health Officers (analytics dashboard consumers)
- Regulatory: Ministry of Health and Family Welfare, CDSCO, DPDPA compliance reviewers
- Academic: CS and healthcare researchers, journal reviewers, conference participants

***

## 4. Research Novelty and Contributions

AyushBot's research novelty is grounded in five specific technical contributions, each independently publishable and collectively forming a unified system paper.

### Contribution 1 — EdgeRAG at Clinical Parity with Cloud

The claim that clinical knowledge retrieval at the edge can match cloud-hosted RAG performance, within 2 to 3% retrieval recall, using a combination of HNSW graph indexing, product-quantized FAISS compression, and cross-encoder reranking. This has not been demonstrated for primary-care triage in any prior publication, and the demonstration of sub-3-second time-to-first-token on a Raspberry Pi 4 class device constitutes a novel systems contribution.

### Contribution 2 — Multi-Agent Specialization for Clinical Reasoning

The demonstration that decomposing clinical triage reasoning across five bounded, specialized agents — each with a defined input contract, specific algorithmic tooling, and validated output schema — measurably improves diagnostic accuracy over single-LLM baselines. Prior work uses monolithic LLMs or simple RAG-augmented chat, not state-machine multi-agent orchestration for healthcare.

### Contribution 3 — FL Under Real Geographic Non-IID Heterogeneity

Prior federated learning evaluations in healthcare use artificially partitioned Dirichlet distributions as a proxy for data heterogeneity. AyushBot is the first system to construct non-IID FL evaluation splits derived from actual district-level disease burden data from NFHS-5, India's largest national health survey. This makes the FL evaluation empirically grounded in real epidemiological patterns.

### Contribution 4 — TinyML-to-Agentic Vertical Integration

The architecture spans from a 4 KB inference model on an Arduino microcontroller to a 3.8-billion-parameter SLM on a Raspberry Pi edge gateway, with both layers contributing to a unified clinical decision. No prior published CHW system has demonstrated this vertical integration from hardware-level sensor intelligence to edge-native LLM reasoning.

### Contribution 5 — Curriculum-Integrated Deeptech for Global Health Equity

AyushBot is designed so that every major architectural component maps explicitly to undergraduate CS coursework. The system provides a reusable educational platform where theory — Dijkstra's algorithm, HNSW graph search, FedProx optimization, propositional logic — is learned through real implementation for one of the world's most urgent healthcare access problems.

***

## 5. System Architecture Overview

The system is organized as five operational layers in a strict hierarchy. Each layer functions autonomously when the layer above it is unavailable, ensuring that the entire system degrades gracefully rather than failing catastrophically under rural connectivity conditions.

**Layer 1 — Patient and Household:** The physical environment of assessment. No computing occurs at this layer. The ASHA worker is the human bridge between the patient and the system.

**Layer 2 — Arduino Sensor Pack:** A low-cost physiological sensing unit consisting of pulse-oximetry, digital temperature, and weight sensing modules connected to an Arduino Nano 33 BLE Sense microcontroller running a TinyML danger-sign classifier. The sensor pack communicates with the ASHA's phone via BLE and can raise hardware-level alarms independently.

**Layer 3 — ASHA Android Application:** A Kotlin-based native Android application that serves as the ASHA's primary interface. It handles patient profile creation, BLE sensor integration, symptom checklist recording, voice input, local case storage, Wi-Fi synchronization with the gateway, and delivery of AI-generated recommendations via screen and voice.

**Layer 4 — PHC Edge Gateway:** A Raspberry Pi 4 (8 GB RAM) running a Docker Compose stack of microservices. This is the system's intelligence layer. It hosts the five-agent orchestrator, the EdgeRAG pipeline (embedding model, HNSW index, cross-encoder reranker, and Phi-3 Mini 4-bit), the local FL aggregator, and the MQTT message broker. It communicates with ASHA phones via local Wi-Fi and with the cloud via delayed batch synchronization.

**Layer 5 — Cloud FL Server:** A minimal cloud server responsible only for global federated model aggregation, model versioning, and a health analytics dashboard for district-level health officers. Raw patient data never reaches this layer. Only privatized gradient updates and aggregated statistics flow upward.

The data plane ensures that identifiable patient information stays at Layer 3 or below. The control plane carries model updates, configurations, and aggregated analytics. The communication plane carries encrypted, compressed gradient packets in a store-and-forward pattern from Layer 4 to Layer 5.

***

## 6. Functional Requirements by Layer

### Layer 2 — Sensor Pack

**FR-S1:** The sensor pack must capture SpO₂ with accuracy within ±2% of a clinical pulse oximeter reference across the range 80% to 100%.

**FR-S2:** The sensor pack must capture heart rate with accuracy within ±5 BPM across the range 40 to 200 BPM.

**FR-S3:** The sensor pack must capture body temperature with accuracy within ±0.5°C using the DS18B20 digital thermometer.

**FR-S4:** The sensor pack must support infant and child weight measurement via an HX711-based load cell with accuracy within ±50 grams across 0 to 20 kg.

**FR-S5:** The TinyML model must classify danger-sign presence within 5 milliseconds of reading acquisition without any external communication.

**FR-S6:** The sensor pack must produce a hardware-level audible alarm for danger-sign events (SpO₂ < 90%, HR > 150 BPM, or temperature > 40°C) without requiring phone or gateway connectivity.

**FR-S7:** Battery life must exceed 8 hours of continuous active monitoring on a 1200 mAh LiPo cell at 18 mW average power draw.

**FR-S8:** The complete sensor pack BOM (excluding enclosure) must cost less than ₹3,500 (approximately US$42).

**FR-S9:** The sensor pack must transmit readings over Bluetooth Low Energy (BLE 5.0) using the GATT protocol with ASCON-128 lightweight authenticated encryption.

### Layer 3 — ASHA Android Application

**FR-A1:** The application must function fully offline with zero network calls in the critical triage path.

**FR-A2:** The application must support BLE pairing with the sensor pack and display live SpO₂, heart rate, and temperature readings with a signal quality indicator.

**FR-A3:** The application must support a 20-item IMCI-derived symptom checklist presented with icons and a minimum of 3 Indian regional languages.

**FR-A4:** The application must support voice input for free-form symptom description in at least Hindi, Bengali, Tamil, and Kannada, transcribing audio via on-device ASR.

**FR-A5:** The application must persist all patient cases in a local SQLite database, never deleting records without explicit ASHA confirmation.

**FR-A6:** The application must display a four-tier risk badge (Green/Yellow/Red/Critical) prominently on the case result screen.

**FR-A7:** The application must display the top 2 to 3 differential diagnoses with plain-language explanations and explicit source citations for each.

**FR-A8:** The application must display the recommended action plan (home management, PHC referral, or emergency evacuation) with facility name and routing instructions.

**FR-A9:** The application must generate a pre-filled digital referral slip exportable as a PDF or shareable via WhatsApp.

**FR-A10:** The application must play a voice-synthesized recommendation in the ASHA's preferred local language via the AI4Bharat TTS engine.

**FR-A11:** The application must detect PHC local Wi-Fi and silently sync pending cases and FL updates to the gateway in the background.

**FR-A12:** The application must support ABHA (Ayushman Bharat Health Account) ID entry for patient identity linkage without mandating it.

### Layer 4 — PHC Gateway

**FR-G1:** The gateway must serve 10 to 20 concurrent ASHA connections over local Wi-Fi without dropping MQTT messages.

**FR-G2:** The gateway must respond to a complete triage request (from ASHA query submission to first token delivery) within 4 seconds under full load.

**FR-G3:** The gateway must run all Docker microservices (MQTT broker, EdgeRAG service, FL aggregator, sync API) simultaneously within 8 GB RAM.

**FR-G4:** The EdgeRAG subsystem must achieve Recall@5 of at least 0.85 on the clinical protocol corpus.

**FR-G5:** The multi-agent orchestrator must produce a structured, citation-backed diagnosis JSON object for every completed case.

**FR-G6:** The gateway must store at least 90 days of case history for local analytics without external storage dependency.

**FR-G7:** The FL aggregator must execute nightly sync within the 2:00 AM to 3:00 AM window when a 3G or better connection is detected.

**FR-G8:** The gateway must apply DP gradient sanitization before any model update leaves the gateway's network boundary.

**FR-G9:** The gateway must support hot-swapping of model weights when a new global model arrives from the cloud, without interrupting ongoing ASHA queries.

**FR-G10:** The gateway must run on a standard PHC power supply with UPS battery backup covering at least 4 hours of operation.

### Layer 5 — Cloud FL Server

**FR-C1:** The cloud server must aggregate gradient updates from at least 5 PHC gateways using FedProx or SCAFFOLD algorithm.

**FR-C2:** The cloud server must maintain a versioned model registry with rollback capability to any prior model generation.

**FR-C3:** The cloud server must detect Byzantine gradient anomalies using Krum aggregation and quarantine suspected poisoned updates.

**FR-C4:** The cloud server must expose a district-level analytics API consumed by the health officer dashboard.

**FR-C5:** The cloud server must be deployed entirely within India (AWS Mumbai region or equivalent) to satisfy DPDPA 2023 data localization requirements.

***

## 7. The Five-Agent Orchestration System

The multi-agent system is implemented as a LangGraph state machine running on the PHC Gateway. Agents receive and return a shared Patient State Object — a structured JSON document that accumulates information as it passes through the pipeline. No agent may modify state fields outside its own designated namespace.

### Agent 1 — Intake and Pre-Triage Agent

**Purpose:** This agent is the gatekeeper. Its responsibility is to determine whether incoming sensor data is trustworthy enough to use, compute all derived clinical features from raw inputs, and produce an authoritative risk tier that governs the behavior of every downstream agent.

**Signal Validation:** The agent applies a variance-based quality filter to the SpO₂ stream. If the coefficient of variation across the last 10 readings exceeds a 3% threshold, the reading is flagged as unreliable. The ASHA is instructed via the phone UI to remeasure before the pipeline continues. This prevents the entire downstream reasoning chain from being corrupted by a loose sensor.

**Derived Feature Engineering:** From raw readings, the agent computes the Weight-for-Age Z-score (WAZ) by interpolating against embedded WHO Multicentre Growth Reference Study tables. It computes 30-second trend features (delta SpO₂, delta HR). It cross-references patient age (months) against respiratory rate thresholds from WHO age-stratified norms.

**Risk Classification:** The validated and enriched feature vector is passed to the XGBoost triage classifier. Output is a 4-class risk tier: Low, Medium, High, or Critical. For Critical classification, the agent writes an EMERGENCY_ESCALATE flag directly to the state object, which the orchestrator reads before even invoking Agent 2, immediately routing to Agent 3 for emergency referral instructions.

**SHAP Output:** The agent appends the top 3 SHAP feature importance values to the state object. These are consumed by Agent 2 to construct retrieval queries, ensuring that the clinical retrieval is primed by the actual drivers of the risk score rather than generic symptom matching.

**Failure Behavior:** If the XGBoost classifier throws an exception or returns a confidence below 0.4 across all four classes, the agent defaults to High risk and sets a CLASSIFIER_UNCERTAIN flag. This prevents silent under-triage.

### Agent 2 — Differential Diagnosis and Knowledge Agent

**Purpose:** This agent is the clinical reasoner. It is the only agent that interacts with the EdgeRAG pipeline and the Phi-3 Mini language model. Its sole output is a ranked, cited differential diagnosis.

**Query Generation:** The agent constructs 2 to 3 targeted retrieval queries from the Patient State Object. This is not a template-filling operation — it uses a structured prompt to the LLM that asks it to generate diverse, semantically distinct sub-queries from the clinical picture. Diversity is essential because different symptom combinations may retrieve different protocol sections.

**Retrieval:** Each sub-query is embedded by all-MiniLM-L6-v2 and searched in the HNSW index. Top-20 results per sub-query are retrieved and deduplicated to approximately 40 unique candidate chunks.

**Reranking:** The cross-encoder scores all 40 (query, chunk) pairs jointly. The top-5 scoring chunks are selected and passed as grounded context to Phi-3 Mini.

**Synthesis:** Phi-3 Mini receives a strictly constrained prompt: it must only use information from the provided chunks, must cite the source of every diagnostic claim by chunk reference number, and must output a structured JSON object conforming to a defined schema. If retrieved chunk scores are all below a minimum relevance threshold, the agent outputs an INSUFFICIENT_EVIDENCE flag rather than attempting an unsupported diagnosis.

**Output Schema:** The agent writes to the state object: primary diagnosis, confidence level, up to 3 alternative diagnoses, active danger signs identified, cited source passages for each diagnostic claim, and a plain-language reasoning summary.

### Agent 3 — Referral Planning and Facility Routing Agent

**Purpose:** This agent is the logistician. It converts the Diagnosis Agent's probabilistic output into a deterministic, actionable care plan. No language model is involved in this agent's core logic — it is entirely rule-based and graph-algorithmic.

**Triage Decision Logic:** A strict propositional rule set determines the care tier. If the diagnosis JSON contains any known emergency condition (severe pneumonia, septic shock, severe acute malnutrition with complications, neonatal danger signs), or if the risk tier is Critical or High, the agent selects the hospital referral tier. Medium-risk cases with home management protocols in the NLEM are directed to PHC. Low-risk cases receive home management plans.

**Facility Routing:** The agent queries a locally stored, geo-referenced graph of the district's health infrastructure. Nodes are village health posts, sub-centres, PHCs, Community Health Centres (CHCs), and district hospitals. Edge weights combine physical road distance, estimated travel time, and a facility load factor updated by the previous FL sync batch. Dijkstra's algorithm finds the optimal destination — not the geographically nearest facility, but the optimal one that is accessible, appropriately equipped, and not currently overwhelmed.

**Drug Dosage Calculation:** The agent performs a secondary RAG lookup constrained entirely to the National List of Essential Medicines (NLEM) knowledge base partition. From the matched protocol, it extracts weight-based dosage instructions and calculates the exact dose for the child's confirmed weight.

**Referral Slip Generation:** The agent generates a structured referral document containing patient demographics (pseudonymized), ASHA ID, presenting vitals, working diagnosis, pre-referral medications given, recommended facility, and transport recommendation (ambulance vs. self-referral).

**Failure Behavior:** If Dijkstra's routing returns no reachable facility within a defined distance threshold, the agent escalates to district emergency medical services (108 ambulance trigger via SMS) and flags the case for immediate human review by the PHC medical officer.

### Agent 4 — FL Participation and Sync Agent

**Purpose:** This agent is the asynchronous learner. It runs in the background, entirely decoupled from the live triage pipeline. It is responsible for training, privacy protection, compression, and synchronization of model updates.

**Trigger Conditions:** The agent monitors the local SQLite case store. It activates when a threshold number of high-confidence completed cases have accumulated and when the gateway's CPU temperature and active query load are within safe limits. It never preempts a live triage request.

**Local Training:** The agent runs SGD-based fine-tuning of the XGBoost triage classifier and the LoRA adapter layer of the all-MiniLM-L6-v2 embedding model for 3 to 5 epochs on the local case batch.

**Differential Privacy:** The agent applies gradient clipping (scaling the gradient vector's L2-norm to a maximum threshold) and then injects calibrated Gaussian noise. The noise variance is calculated to satisfy the target epsilon-delta differential privacy budget. This mathematically guarantees that no individual patient's data can be reverse-engineered from the transmitted gradient packet.

**Compression:** The privatized gradient tensor is compressed from float32 to ternary representation, reducing payload size from several megabytes to approximately 50 KB.

**Store-and-Forward:** The compressed, encrypted packet is written to a durable transmission queue. The agent polls for an internet-reachable path. When a stable connection is detected in the designated nightly sync window, it negotiates TLS 1.3 mutual authentication with the cloud server and transmits the payload. On receiving the aggregated global model delta, it hot-swaps the model weights in the agent runtime without system restart.

**Byzantine Defense:** If the cloud's acknowledgment contains a model delta whose cosine distance from the previous global model exceeds a defined threshold, the agent treats the update as potentially corrupted and requests re-delivery before applying it.

### Agent 5 — Language and Accessibility Agent

**Purpose:** This agent is the cross-lingual bridge. It operates at both the input and output ends of the pipeline, and its quality directly determines whether the system is usable by the actual target population.

**Input Direction — Intent Classification:** After the ASHA's voice input is transcribed, IndicBERT classifies the intent of the utterance (Symptom Report, Drug Query, Referral Question) to route it correctly within the pipeline. It also performs Named Entity Recognition, extracting clinical entities such as disease names, body parts, symptoms, and drugs from the local-language text.

**Input Direction — Translation:** Extracted clinical entities and free-form descriptions are translated from the regional language to standardized English medical terminology using IndicTrans2, which has been fine-tuned on ASHA training module translations and IMCI chapter translations to produce medically accurate rather than literally translated output.

**Output Direction — Back-Translation:** The final care plan, diagnosis explanation, and referral instructions produced in English by Agent 3 are translated back to the ASHA's preferred regional language. Medical term grounding is applied: complex terms are replaced with community-understood health concepts where a direct translation would be meaningless.

**Output Direction — TTS Delivery:** The translated text is synthesized into natural speech by the AI4Bharat TTS engine supporting 13 Indian languages, and sent to the ASHA's phone for audio playback alongside the visual risk badge and structured recommendation text.

***

## 8. ML Model Pipeline Requirements

**MLR-1:** The TinyML classifier on the Arduino must occupy less than 6 KB of flash storage and achieve minimum sensitivity of 0.95 for SpO₂ < 90% danger events.

**MLR-2:** The XGBoost pre-triage classifier must be trained on MIMIC-IV ICU cohort data and fine-tuned on NFHS-5 Indian child health records, producing an AUC of at least 0.79 on India-calibrated evaluation splits.

**MLR-3:** XGBoost SHAP explanations must be computed at every inference call and the top-3 contributing features must be appended to the Patient State Object for Agent 2 consumption.

**MLR-4:** The dense bi-encoder (all-MiniLM-L6-v2) must embed 1,487 clinical protocol chunks offline and store the resulting HNSW index in a format that fits within 3 MB uncompressed.

**MLR-5:** The cross-encoder reranker must process up to 40 candidate (query, passage) pairs within 400 milliseconds on the Raspberry Pi 4.

**MLR-6:** Phi-3 Mini at 4-bit quantization must occupy no more than 2.5 GB of RAM and produce first-token output within 2 seconds after receiving a fully assembled prompt.

**MLR-7:** Phi-3 Mini must produce structured JSON output conforming to the diagnosis schema on 100% of valid requests. Invalid JSON must trigger automatic re-generation with a temperature reduction.

**MLR-8:** IndicBERT fine-tuned on IHQID must achieve intent classification F1 of at least 0.85 across Hindi, Bengali, Tamil, and Kannada.

**MLR-9:** IndicTrans2 must achieve BLEU scores consistent with AI4Bharat's published benchmarks on medical domain translation pairs used in the corpus.

**MLR-10:** The complete ML inference pipeline (from ASHA query submission to final JSON delivery to the phone) must complete within 4 seconds at the 95th percentile under full gateway load.

***

## 9. EdgeRAG Subsystem Requirements

The EdgeRAG subsystem is the technical centerpiece of AyushBot's knowledge-grounding mechanism.

### 9.1 Corpus Requirements

The knowledge corpus must cover the following authoritative sources in their most recent editions: MoHFW Standard Treatment Workflows for Primary and Secondary Healthcare, WHO IMCI Pocket Book (3rd edition), NHM ASHA Training Modules 6 and 7, National List of Essential Medicines (NLEM), NCAP-CH Child Health Guidelines, and BIS/WHO Drinking Water Quality Standards.

Chunking must respect semantic section boundaries and produce chunks of 400 to 600 tokens with 50-token overlapping windows. Every chunk must carry metadata: source name, section heading, page number, ICD-10 codes mentioned, drug names (normalized to WHO INN), and a priority flag for IMCI danger sign criteria chunks.

The resulting indexed corpus must contain no fewer than 1,200 and no more than 2,000 chunks to balance coverage against retrieval precision.

### 9.2 Retrieval Performance Requirements

- Recall@5: ≥ 0.85 on a hand-labeled test set of 200 clinical triage queries
- Recall@10: ≥ 0.91
- MRR (Mean Reciprocal Rank): ≥ 0.65
- HNSW retrieval latency (top-40 candidates): ≤ 200 ms
- Cross-encoder reranking latency (40 candidates): ≤ 400 ms
- Total TTFT (query to LLM first token): ≤ 3,000 ms

### 9.3 Query Generation Requirements

Agent 2 must generate 2 to 3 semantically diverse sub-queries per case, with at least one sub-query explicitly covering the highest SHAP-contributing feature from the triage classifier. Sub-queries must be in English (post-translation by Agent 5) and must be at most 50 tokens in length to keep embedding computation latency below 100 ms.

***

## 10. Federated Learning Subsystem Requirements

### 10.1 FL Algorithm Requirements

**FLR-1:** The default FL algorithm must be FedProx with proximal regularization parameter μ = 0.01, which constrains local updates from diverging too far from the global model — addressing the documented accuracy degradation of FedAvg under non-IID geographic disease distributions.

**FLR-2:** The system must support optional SCAFFOLD algorithm deployment for high-bandwidth PHC nodes, as SCAFFOLD's control-variate correction achieves higher convergence speed at the cost of approximately 8% additional communication overhead.

**FLR-3:** The cloud aggregator must implement Krum Byzantine-fault-tolerant aggregation as a secondary aggregation mode, activating automatically when any incoming gradient update's L2 distance from the cluster centroid exceeds 3 standard deviations.

### 10.2 Differential Privacy Requirements

**FLR-4:** Gradient clipping norm threshold C must be set to 1.0 for all local training runs.

**FLR-5:** Gaussian noise standard deviation must be calculated via the formula: σ = C × sqrt(2 × ln(1.25 / δ)) / ε, targeting ε = 1.0 to 1.5 and δ = 10⁻⁵. This corresponds to σ ≈ 1.13, consistent with production FL systems such as Google Gboard.

**FLR-6:** Cumulative privacy budget across T rounds must be tracked via Rényi Differential Privacy composition and must not exceed ε = 2.0 across the entire deployment lifetime of a PHC node.

**FLR-7:** Gradient quantization must reduce payload size to ≤ 100 KB per round per gateway node, ensuring transmission viability over 2G EDGE connections (minimum effective throughput: 100 Kbps).

### 10.3 Non-IID Evaluation Requirements

**FLR-8:** The FL evaluation must use NFHS-5-derived district disease distribution clusters (minimum 5 clusters corresponding to distinct Indian epidemiological regions) to partition the training data among simulated FL nodes, producing Dirichlet α = 0.1 label skew as the worst-case evaluation condition.

**FLR-9:** The FL system must demonstrate convergence to within 5% of a centralized-training baseline within 10 rounds under the α = 0.1 non-IID condition.

**FLR-10:** Communication efficiency must be reported as total megabytes transmitted per node per round for all algorithm variants.

***

## 11. IoT Hardware Requirements (Course: Internet of Things and Applications)

This section maps the IoT course syllabus to AyushBot's specific hardware design requirements.

### 11.1 Sensor Selection and Justification

**Pulse Oximetry (Unit II — Sensing):** The MAX30100 or MAX30102 sensor uses dual-wavelength photoplethysmography (PPG) at 660nm and 940nm. Red and infrared light absorbance ratios across arterial blood allow calculation of oxygen saturation via the Beer-Lambert law. This is directly applicable to IoT course content on sensor types and data acquisition.

**Temperature (Unit II — Sensing):** DS18B20 uses a 1-Wire digital bus protocol, eliminating analog frontend noise and demonstrating the IoT principle of digital over analog sensing for precision medical applications.

**Weight (Unit II — Sensing and Actuation):** HX711 is a 24-bit precision analog-to-digital converter interfaced with a strain-gauge load cell. It demonstrates bridge circuit ADC design concepts from the IoT syllabus.

**Microcontroller (Unit III — Arduino/RPi):** Arduino Nano 33 BLE Sense (nRF52840, Cortex-M4, 64 MHz) is explicitly an IoT course-aligned platform. Its onboard BLE 5.0 module removes the need for external wireless modules. This directly demonstrates the embedded IoT programming covered in Unit III.

**Edge Gateway (Unit V — Smart IoT Systems):** Raspberry Pi 4 is the canonical IoT edge gateway platform and is directly referenced in IoT course Unit III and Unit V content. Running Docker Compose on the RPi 4 demonstrates smart IoT application deployment.

### 11.2 BLE Communication Stack

The BLE GATT (Generic Attribute Profile) communication between the sensor pack and the ASHA phone demonstrates IoT connectivity protocols from the course syllabus. The sensor pack exposes three GATT Characteristics (SpO₂, HR, Temperature) under a custom Healthcare Service UUID. Notifications are sent at 5-second intervals. Weight data is entered manually via the ASHA app and linked to the BLE session by pairing ID.

ASCON-128 lightweight symmetric-key authenticated encryption is applied at the BLE application layer (above the BLE security layer). ASCON was selected by NIST as the standard for lightweight cryptography in 2023 and is specifically designed for microcontroller-class devices with 256-byte RAM overhead.

### 11.3 MQTT Protocol Stack (Unit IV — Networking for IoT)

The ASHA phone to PHC Gateway communication uses MQTT v5.0 over local Wi-Fi with TLS 1.3. MQTT is the canonical IoT application-layer protocol and appears explicitly in the IoT course Unit IV. The system demonstrates MQTT QoS Level 1 (at-least-once delivery) for triage requests, ensuring no case is silently dropped, and QoS Level 0 (fire-and-forget) for telemetry streams where occasional loss is acceptable.

Emergency alerts (Critical risk tier cases) use MQTT Retain flags so that the gateway stores and immediately re-delivers the alert to any ASHA client that reconnects after a brief disconnection.

### 11.4 TinyML (Advanced IoT — Unit V Edge Computing)

TinyML is explicitly a frontier application of the IoT edge computing content in Unit V. The quantized decision tree compiled via Edge Impulse to INT8 for the Arduino demonstrates the complete TinyML workflow: model training on a PC, export, quantization, compilation, and deployment to a microcontroller with inference latency measurement. This is a publishable technical demonstration in its own right.

***

## 12. Computer Networks Requirements (Course: Computer Networks)

AyushBot's communication architecture provides live demonstrations of multiple CN course modules.

### 12.1 Network Stack Across System Layers

**Arduino to Phone (BLE GATT):** Operates at the physical and data-link layers. Demonstrates wireless channel access, GATT protocol stack, and BLE 5.0 connection parameter negotiation. Maps to CN Unit I and Unit II content on data link layer and wireless LANs.

**Phone to Gateway (Wi-Fi MQTT/TLS 1.3):** Operates across the physical, data-link, network, transport, and application layers. Demonstrates the complete TCP/IP stack, TLS 1.3 handshake and session resumption, and MQTT application layer protocol. Maps to CN Units II through IV.

**Gateway to Cloud (QUIC mTLS, asynchronous batch):** Uses QUIC (Quick UDP Internet Connections), a multiplexed, encrypted transport protocol designed for high-latency, packet-loss-prone links (rural internet). QUIC's 0-RTT reconnect is critical for intermittent rural connectivity. Maps to CN Unit III transport layer content.

### 12.2 Delay-Tolerant Networking (DTN)

The store-and-forward synchronization pattern used by Agent 4 is a direct implementation of Delay-Tolerant Networking (DTN) architecture, a network paradigm designed for environments with intermittent connectivity and long link latency. The system implements the Bundle Protocol concept: data is encapsulated in bundles with delivery guarantees, stored durably on the local filesystem when the next-hop link is unavailable, and forwarded when connectivity resumes.

This maps directly to CN Unit IV application layer content and provides a real-world demonstration of disruption-tolerant routing that goes beyond the textbook examples.

### 12.3 TCP Congestion Control (Classroom Demonstration)

When 10 to 20 ASHA workers simultaneously sync their cases upon arriving at a PHC, the Raspberry Pi 4's network interface becomes a bottleneck. The gateway's MQTT broker and TCP stack experience concurrent connection bursts, triggering TCP slow-start, congestion window growth, and potential AIMD (Additive Increase Multiplicative Decrease) behavior. This is a live, measurable demonstration of CN Unit III congestion control algorithms.

### 12.4 Quality of Service (QoS) Differentiation

Emergency alert MQTT messages (Critical risk tier) are published with a high-priority flag. The Mosquitto broker is configured with a priority queue that processes Critical-flagged messages before routine case submissions. This is a practical DiffServ (Differentiated Services) implementation demonstrating CN Unit III QoS concepts.

### 12.5 Security: TLS 1.3 and Mutual Authentication

All gateway-to-cloud communication uses TLS 1.3 with mutual authentication (mTLS), where both the client (gateway) and server (cloud) present certificates. This maps to CN Unit V network security content: certificate authorities, X.509 certificates, TLS handshake, and authenticated key exchange.

***

## 13. Algorithms Requirements (Course: Design and Analysis of Algorithms)

### 13.1 Dijkstra's Algorithm — Facility Routing

**Application:** Agent 3 uses Dijkstra's single-source shortest-path algorithm on a weighted, directed graph of district health infrastructure. The graph has approximately 50 to 200 nodes (village health posts, sub-centres, PHCs, CHCs, district hospitals) and edges weighted by a composite of road distance, travel time, and facility load factor.

**Algorithmic Details:** Standard Dijkstra with a min-heap priority queue achieves O((V + E) log V) time complexity. The facility graph is sparse (average degree ≈ 3 to 5), so E ≈ 3V and the complexity is approximately O(V log V). For a 200-node district graph, this executes in microseconds on the RPi 4.

**Course Mapping:** Directly maps to DAA Unit IV greedy algorithms. Students can analyze the optimality proof for Dijkstra (greedy choice property, optimal substructure) and verify that the single-source shortest path is correctly computed by tracing the algorithm on the actual district graph.

**Research Extension:** The edge weight function is dynamic. Facility load is updated by the FL sync cycle, meaning the graph is a time-varying weighted graph. The research contribution is demonstrating that even a simple Dijkstra implementation over a dynamically reweighted graph outperforms static nearest-facility routing in terms of patient wait time and travel efficiency.

### 13.2 HNSW — Graph-Based Approximate Nearest Neighbor Search

**Application:** The EdgeRAG subsystem uses HNSW (Hierarchical Navigable Small World) graphs for sub-linear approximate nearest neighbor search over the 1,487 clinical protocol chunk embeddings.

**Algorithmic Details:** HNSW builds a multi-layer graph where Layer 0 contains all vectors and higher layers contain exponentially sparse subsets acting as routing shortcuts. At query time, greedy search begins at the sparsest highest layer, descending to Layer 0. With M = 16 and ef_search = 50, the algorithm evaluates approximately 50 candidate nodes at Layer 0 regardless of corpus size. This reduces time complexity from O(N) linear scan to O(log N) expected with O(log N) index space.

**Course Mapping:** Maps to DAA Unit I (asymptotic analysis), Unit II (graph representations), and Unit IV (greedy graph search algorithms). Students can analyze the Recall-Speed trade-off curve by varying ef_search and plot empirical versus theoretical O(log N) complexity.

### 13.3 0/1 Knapsack — FL Client Selection

**Application:** When the PHC gateway has limited bandwidth (common on rural connections), the FL Sync Agent must select which subset of local micro-model components to transmit in a single sync window to maximize aggregate learning contribution within the bandwidth budget.

**Formulation:** Each model component (XGBoost gradient, MiniLM LoRA adapter delta, cross-encoder fine-tune layer) has a weight (transmission size in KB) and a value (estimated improvement contribution measured by local validation loss reduction). The bandwidth budget is the knapsack capacity. The goal is to select the subset of components that maximizes total value within capacity — a classic 0/1 Knapsack.

**Course Mapping:** Maps to DAA Unit IV dynamic programming algorithms. The DP table formulation, O(nW) solution, and traceback are directly demonstrable on this concrete real-world instance.

### 13.4 Asymptotic Analysis — Comparing Retrieval Strategies

**Application:** The research contribution of EdgeRAG requires a formal asymptotic comparison between retrieval approaches: brute-force O(N) flat scan, IVF (Inverted File Index) O(N/nlist) partitioned scan, and HNSW O(log N) graph traversal. For N = 1,487, differences are empirically measurable and theoretically analyzable.

**Course Mapping:** Maps to DAA Unit I (Big-O, Omega, Theta notation). Students perform empirical runtime measurements for each retrieval strategy across corpus sizes (100, 500, 1000, 1487 chunks) and verify theoretical growth rates.

### 13.5 Greedy Algorithm — FedProx Client Selection

**Application:** The cloud FL server implements a greedy client selection strategy for choosing which PHC gateways participate in each aggregation round. Gateways are ranked by a composite score (estimated gradient quality × inverse communication cost). The greedy algorithm selects the top-K gateways maximizing total expected information gain within the aggregation round's time budget.

**Course Mapping:** Maps to DAA Unit IV greedy algorithms and activity selection problem variants.

***

## 14. Discrete Mathematics Requirements (Course: Discrete Mathematical Structures and Combinatorics)

### 14.1 Propositional Logic — Clinical Triage Rules

**Application:** Agent 1's escalation logic and Agent 3's referral tier decision are formalized as propositional logic expressions. Example: `EMERGENCY ← (SpO₂ < 88) ∨ (HR > 160 ∧ Temperature > 39.5) ∨ (Convulsions = True) ∨ (WAZ < -3 ∧ Edema = True)`. These logical expressions are compiled directly into the agent's rule evaluation engine.

**Course Mapping:** Maps to Discrete Math Unit II (propositional calculus, logical connectives, tautologies). Students can express the complete IMCI danger-sign criteria as a propositional formula, construct its truth table, apply De Morgan's laws to simplify compound conditions, and verify logical equivalence between IMCI protocol text and the formalized rule.

### 14.2 Partial Orders and Hasse Diagrams — Differential Ranking

**Application:** The differential diagnosis output from Agent 2 is not simply a sorted list; it is a partial order. Two diagnoses may be logically incompatible (Severe Pneumonia and Non-Severe Pneumonia cannot both be true simultaneously) while a third diagnosis (Severe Malnutrition with Pneumonia) may dominate both in clinical severity. This dominance relation is a partial order, which can be visualized as a Hasse diagram.

**Course Mapping:** Maps to Discrete Math Unit III (relations, partial orders, Hasse diagrams). The project provides a concrete, clinically meaningful partial order for students to formalize, draw, and reason about.

### 14.3 Recurrence Relations — FL Convergence Modeling

**Application:** The convergence of FedProx across rounds follows a recurrence relation. If Aₜ denotes the test accuracy after round t, then Aₜ₊₁ ≈ Aₜ + c × (A* − Aₜ) × f(μ), where A* is the converged accuracy and c × f(μ) is the per-round learning rate damped by the proximal term. This first-order linear recurrence can be solved in closed form to predict convergence behavior.

**Course Mapping:** Maps to Discrete Math Unit I (sequences, mathematical induction, recurrence relations). Students derive and solve the convergence recurrence, then validate predicted round-to-convergence counts against empirical FL training curves.

### 14.4 Coding Theory — Fuzzy Symptom Matching

**Application:** ASHAs sometimes misspell disease or drug names when entering text. The system uses Hamming distance and edit distance (Levenshtein) to match imprecise inputs to the nearest canonical clinical term in the medical term normalization layer. Example: "amoxycillin" → "amoxicillin" via Levenshtein distance 2.

**Course Mapping:** Maps to Discrete Math Unit IV (coding theory, Hamming distance). Students calculate Hamming and edit distances between misspelled and canonical medical terms, determine minimum distance bounds for a medical vocabulary dictionary, and analyze the computational complexity of building a BK-tree for efficient fuzzy matching.

### 14.5 Graph Theory — Health Facility Network

**Application:** The district health facility network used by Agent 3's Dijkstra routing is a weighted, directed graph. Its properties (connectivity, strongly connected components, eccentricity of each node, diameter of the district health graph) are meaningful clinical quantities. For example, graph diameter corresponds to the maximum minimum travel time from the most isolated village to any facility.

**Course Mapping:** Maps to Discrete Math Unit III (graphs, graph properties, connectivity, paths). Students analyze the structural properties of the district health graph and interpret them in clinical context.

***

## 15. Dataset Requirements

### 15.1 MIMIC-IV (PhysioNet)

**Source:** Beth Israel Deaconess Medical Center, 2008–2019. De-identified. 299,712 ICU admissions.

**Access:** Free with completion of PhysioNet CITI Human Subjects Research credentialing (2 to 3 business days).

**Usage in AyushBot:** Cohort extraction of 70,341 ICU admissions with complete first-2-hour vital signs for XGBoost pre-training. Also used for TinyML classifier training and Health Gym synthetic augmentation derivation.

**Ethical Requirement:** Every team member must individually complete CITI credentialing before accessing MIMIC-IV. Data must not be stored outside the designated research workstation.

### 15.2 NFHS-5 (DHS Program)

**Source:** International Institute for Population Sciences and Ministry of Health, Government of India. 2019–2021 survey. 636,699 households, 232,920 children.

**Access:** Freely downloadable from the DHS Program public data portal, no institutional DUA required.

**Usage in AyushBot:** Fine-tuning the XGBoost classifier on India-calibrated pediatric health features. Construction of non-IID district FL evaluation splits. WAZ z-score distribution validation.

### 15.3 IHQID (ACL Anthology)

**Source:** ACL Anthology 2023 publication. 7,200 healthcare queries across 6 Indian languages with intent and entity annotations.

**Access:** Open access via ACL Anthology.

**Usage in AyushBot:** Fine-tuning IndicBERT for intent classification and NER in the multilingual input pipeline.

### 15.4 Health Gym (JMIR)

**Source:** JMIR Medical Informatics 2024. Synthetic health datasets derived from MIMIC-IV via generative modeling.

**Access:** Open-source on GitHub.

**Usage in AyushBot:** Augmenting rare critical cases (severe hypotension, septic shock) that are underrepresented in the primary-care-focused training corpus.

### 15.5 RAG Corpus (Public PDFs)

All clinical protocol documents are publicly available as downloadable PDFs from official government and WHO websites. No DUA or credential required. Specific documents: MoHFW STW for 50+ primary care conditions, WHO IMCI Pocket Book (3rd edition, 2023), NHM ASHA Training Modules 6 and 7, NLEM 2022, NCAP-CH guidelines, BIS 10500 drinking water standard.

***

## 16. Non-Functional Requirements

**NFR-1 — Latency:** End-to-end triage response (ASHA submits case → recommendation delivered to phone): ≤ 4 seconds at the 95th percentile under 15 concurrent ASHA connections.

**NFR-2 — Availability:** PHC Gateway uptime ≥ 99.5% measured across any 30-day window (approximately 3.6 hours permissible downtime per month). Achieved via UPS battery, Docker container auto-restart, and daily automated health checks.

**NFR-3 — Offline Durability:** The system must support at least 7