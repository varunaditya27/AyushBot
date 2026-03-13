# AyushBot: The Multi-Agent Orchestration Architecture
## Comprehensive End-to-End Technical Deep Dive

## 1. Architectural Philosophy: Why Multi-Agent?

In healthcare AI, deploying a single, monolithic Large Language Model (LLM) to handle patient intake, diagnosis, logistical routing, and language translation simultaneously is a catastrophic anti-pattern. Monolithic models suffer from context dilution, severe hallucination risks, and an inability to reliably separate probabilistic reasoning (guessing a diagnosis) from deterministic logic (calculating a drug dosage or routing a referral).

AyushBot solves this by employing a **Multi-Agent State Machine Architecture** deployed at the edge (on a Raspberry Pi 4 Gateway). Inspired by frameworks like LangGraph, the system models clinical triage as a Directed Acyclic Graph (DAG). Five highly specialized, strictly bounded autonomous agents pass a shared "Patient State Object" between them. Each agent has a singular mandate, a defined input contract, specific algorithmic tooling, and a rigorously validated output structure. 

This separation of concerns ensures that hallucinations are quarantined, evidence is traceable, and deterministic rules (like emergency escalation) can override probabilistic generation at any time.

***

## 2. The Five Specialized Agents: Technical Grounding

### Agent 1: The Intake & Pre-Triage Agent (The Gatekeeper)
*   **Mandate:** Signal validation, feature engineering, and deterministic risk stratification.
*   **Inputs:** Raw sensor streams (SpO2, Heart Rate, Temperature, Weight) via BLE, alongside structured categorical inputs from the ASHA worker's mobile checklist.
*   **Technical Execution:**
    Before any LLM reasoning occurs, Agent 1 acts as a deterministic and statistical gatekeeper. First, it performs **Signal Quality Filtering**. If the variance of the SpO2 reading exceeds a strict threshold (indicating a loose sensor or patient movement), it flags the data as invalid and halts the flow, prompting the ASHA to re-measure. 
    Next, it computes **Derived Clinical Features**. It cross-references the patient's age and weight against embedded WHO growth standard tables to calculate a Weight-for-Age Z-score (WAZ) for malnutrition screening, and calculates pulse-pressure proxies.
    Finally, it runs these features through an extremely lightweight, quantized XGBoost or Decision Tree classifier (pre-trained on MIMIC-IV and NFHS-5 data). 
*   **Outputs:** It updates the Patient State Object with a definitive Risk Badge (Low, Medium, High, Critical).
*   **Architectural Escalation:** If the output is "Critical" (e.g., SpO2 < 90%), Agent 1 bypasses the diagnostic reasoning layer entirely and triggers an immediate hard-interrupt, routing directly to Agent 3 for emergency evacuation protocols.

### Agent 5: The Language & Accessibility Agent (The Intersecting Interface)
*   *(Note: While numbered 5, this agent intersects the flow at both the very beginning and the very end).*
*   **Mandate:** Bidirectional cross-lingual semantic mapping and intent extraction.
*   **Inputs:** Free-text or voice-transcribed symptom reports in regional Indian languages (Hindi, Bengali, Tamil, etc.), and eventually, the English clinical outputs from the other agents.
*   **Technical Execution:**
    Operating on edge-optimized NLP models (such as AI4Bharat's IndicBERT and IndicTrans2), Agent 5 first performs **Intent Classification and Named Entity Recognition (NER)**. It takes a local-language phrase describing "fast breathing and hot chest," identifies the clinical entities, and translates them into standardized English medical terminologies (e.g., "tachypnea," "febrile"). This ensures the downstream reasoning agents are not confused by colloquial syntax.
    At the end of the pipeline, Agent 5 activates again. It takes the highly technical, English-based differential diagnosis and referral instructions, and translates them back into the ASHA’s native language. It ensures **Medical Term Grounding**—meaning it doesn't just translate literally, but maps complex terms to culturally understood health concepts, finally processing the text through an offline Text-to-Speech (TTS) engine for auditory delivery.

### Agent 2: The Differential Diagnosis & Knowledge Agent (The Clinical Reasoner)
*   **Mandate:** Evidence-backed medical reasoning via EdgeRAG.
*   **Inputs:** The translated, standardized clinical entities and validated vitals from Agent 1 and Agent 5.
*   **Technical Execution:**
    Agent 2 is explicitly banned from relying on its internal parametric memory to diagnose patients. Instead, it functions as an intelligent search orchestrator. 
    First, it generates 2 to 3 highly targeted search queries based on the patient state. It passes these queries through a dense embedding model (like all-MiniLM-L6-v2) to search a local, product-quantized HNSW (Hierarchical Navigable Small World) vector index containing hundreds of pages of Ministry of Health and WHO IMCI clinical protocols.
    To ensure precision, it utilizes a **Cross-Encoder Reranker**. It pairs the top retrieved document chunks with the query and scores their logical relevance, filtering out tangential information. 
    Finally, it feeds the top-ranked, highly relevant protocol chunks into a small, 4-bit quantized LLM (like Phi-3 Mini). The prompt strictly enforces that the LLM must synthesize a differential diagnosis *only* using the provided chunks.
*   **Outputs:** A ranked list of 2-3 potential conditions, accompanied by an explicit citation (e.g., "Source: MoHFW Standard Treatment Guidelines, Page 42").

### Agent 3: The Referral Planning & Facility Routing Agent (The Logistician)
*   **Mandate:** Deterministic action planning, dosage calculation, and geographic routing.
*   **Inputs:** The synthesized diagnosis from Agent 2, the Risk Level from Agent 1, and the geographical location of the ASHA worker.
*   **Technical Execution:**
    Agent 3 bridges the gap between "knowing what is wrong" and "knowing what to do." It applies strict propositional logic. If the diagnosis indicates severe acute malnutrition with medical complications, it triggers the PHC/District Hospital referral protocol. 
    For medication, it performs a secondary RAG lookup specifically constrained to the National List of Essential Medicines (NLEM) to extract exact weight-based pediatric dosages. 
    For routing, Agent 3 utilizes **Dijkstra’s Algorithm** on a locally stored, continuously updated graph of the district’s health infrastructure. The nodes are clinics/hospitals, and the edge weights are a combination of physical distance, current road conditions, and the current patient load of the facility (which is synced via the federated network). 
*   **Outputs:** A highly structured, deterministic action plan—whether that is home management with ORS, or an immediate referral to a specific district hospital 14 kilometers away, complete with a pre-generated digital referral slip.

### Agent 4: The FL Participation & Sync Agent (The Asynchronous Learner)
*   **Mandate:** Privacy-preserving continual learning and network state management.
*   **Inputs:** A batch of completed, fully resolved Patient State Objects stored in the local SQLite database.
*   **Technical Execution:**
    Agent 4 operates asynchronously and parallel to the main triage flow. It constantly monitors the thermal limits of the gateway and network availability (Delay-Tolerant Networking). 
    When idle compute is available, Agent 4 pseudo-labels the recent cases and initiates a local Stochastic Gradient Descent (SGD) fine-tuning loop on the base triage classifiers. It calculates the weight gradients, applies strict **Gradient Clipping**, and injects **Gaussian Noise** to satisfy Differential Privacy (Epsilon-Delta) requirements. 
    It then quantizes these gradients, encrypts them, and places them in a transmission queue. Once the gateway detects stable Wi-Fi, Agent 4 negotiates a secure TLS 1.3 handshake with the cloud server, transmits the privatized gradients, and downloads the newly aggregated global model weights, hot-swapping them into the active memory of Agents 1 and 2 without system downtime.

***

## 3. The End-to-End Orchestration Flow (Lifecycle of a Case)

To understand the perfection of this architecture, one must trace the flow of a single patient encounter through the state machine. 

**Phase 1: The Edge Ingestion (Node Entry)**
The ASHA worker pairs the Bluetooth sensor pack to a child patient. The hardware captures SpO2 and Heart Rate. Concurrently, the ASHA speaks into her phone in Bengali: *"The child has a hot fever and his chest is pulling in when he breathes."*
*Action:* The phone packages this payload and sends it over local Wi-Fi/MQTT to the PHC Gateway. 

**Phase 2: Standardization & Triage (Agent 5 $\rightarrow$ Agent 1)**
The orchestrator awakens. The Patient State Object is instantiated. 
Agent 5 intercepts the audio text. It extracts "febrile" and "chest indrawing," appending these standardized English entities to the State Object.
Agent 1 takes over. It validates the Bluetooth SpO2 variance, confirming a solid reading of 88%. It calculates the algorithms and flags the State Object with `RISK_TIER: CRITICAL`. 

**Phase 3: The Knowledge Retrieval (Agent 2)**
Seeing the Critical flag, the orchestrator simultaneously warns the ASHA UI while invoking Agent 2. 
Agent 2 sees `[SpO2: 88%, tachypnea, chest indrawing]`. It embeds this vector, traverses the HNSW graph, and extracts the exact WHO IMCI protocol for Severe Pneumonia. The 4-bit LLM reads the protocol and updates the State Object with `DIAGNOSIS: Severe Pneumonia (Confidence: 96%) [Citation: IMCI Chart Booklet, Sec 2]`.

**Phase 4: Action & Logistics (Agent 3)**
The orchestrator passes the State Object to Agent 3. 
Agent 3 reads "Severe Pneumonia." It checks the NLEM index for the pre-referral dose of oral amoxicillin based on the child's exact weight (captured by the sensor). Next, it runs Dijkstra’s algorithm on the local facility graph. The nearest PHC is marked as "Doctor absent today" (based on yesterday's sync), so the algorithm calculates the shortest path to the Secondary Community Health Centre. 
Agent 3 appends the dosage and the mapped route to the State Object.

**Phase 5: Localization & Delivery (Agent 5)**
The State Object is now completely filled with highly technical English medical logic. The orchestrator hands it back to Agent 5. 
Agent 5 translates the entire package back into fluent, culturally grounded Bengali. It generates the audio file via TTS. The payload is sent back over MQTT to the ASHA’s Android phone, displaying a red critical badge, the diagnosis, the exact drug dosage, and voice instructions on where to transport the child.
*Total latency:* Under 4 seconds. 

**Phase 6: The Epilogue (Agent 4)**
Hours later, at 2:00 AM, the PHC Gateway is idle. The orchestrator awakens Agent 4. 
Agent 4 retrieves this severe pneumonia case from the database. It uses it to marginally adjust the local XGBoost triage weights to be slightly more sensitive to chest indrawing in children of this specific demographic. It mathematically scrambles the update to ensure the child's identity is erased forever, and quietly sends the mathematical learning vector to the national cloud, ensuring that tomorrow, a model in a neighboring village is just a fraction of a percent smarter. 

***

## 4. State Management and Fault Tolerance

The true power of this multi-agent architecture lies in its fault tolerance. Because it operates as a state machine:
*   **Epistemic Uncertainty Handling:** If Agent 2 retrieves documents but the cross-encoder scores them below a confidence threshold, it refuses to diagnose. It updates the state to `UNKNOWN_ESCALATE`. Agent 3 reads this state and generates a default "Immediate Doctor Consultation Required" instruction, preventing hallucinations.
*   **Graceful Degradation:** If the LLM container (Agent 2) crashes due to a Raspberry Pi thermal throttle, the system does not die. The orchestrator detects the timeout, bypasses Agent 2, and relies entirely on the deterministic risk score from Agent 1 to generate a baseline referral via Agent 3. 

By compartmentalizing statistical NLP, localized graph search, deterministic math, and cryptographic networking into five discrete, perfectly boundaried agents, AyushBot achieves a level of clinical safety, explainability, and hardware efficiency that monolithic AI architectures simply cannot replicate.