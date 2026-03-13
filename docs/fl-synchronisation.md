Here is the comprehensive, end-to-end technical architecture document detailing the Federated Learning (FL) subsystem and its agentic orchestration within AyushBot. 

***

# AyushBot: Federated Learning (FL) & Agentic Synchronization Architecture
## Comprehensive End-to-End Technical Deep Dive

## 1. Architectural Motivation: Why Federated Learning?

In traditional healthcare AI, patient data is centralized in a cloud server to train models. For the AyushBot deployment in rural India, centralized learning is impossible due to three hard constraints:
1. **Regulatory (DPDPA 2023):** Centralizing identifiable or inferable health data violates India’s Digital Personal Data Protection Act. Data must remain at the edge.
2. **Infrastructure:** 87.5% of ASHA workers operate in environments with intermittent, low-bandwidth internet, rendering large data uploads technically unfeasible.
3. **Geographic Heterogeneity (Non-IID Data):** The disease burden in India is highly skewed. A primary health centre (PHC) in Kerala sees vastly different clinical presentations (e.g., tropical fevers) compared to a PHC in Bihar (e.g., severe acute malnutrition). A monolithic global model fails to capture these local nuances without localized fine-tuning.

To solve this, AyushBot utilizes a **Privacy-Preserving Federated Learning** architecture orchestrated by an autonomous agent (**Agent 4: FL Participation & Sync Agent**). Instead of sending data to the cloud, the system sends the model to the data, computes learning gradients locally, and only transmits mathematically noise-injected, aggregated weight updates over the network.

***

## 2. The Agentic Flow: Role of the FL Sync Agent (Agent 4)

Within the PHC Gateway (Raspberry Pi 4), the multi-agent orchestrator runs continuously. While Agents 1, 2, and 3 handle immediate patient triage and diagnosis, **Agent 4** acts as the asynchronous background orchestrator for continuous learning.

Agent 4 is not a passive script; it is a state-aware, autonomous entity with a strict mandate: *Optimize the local model based on new clinical data, protect patient privacy, and navigate network instability to contribute to global intelligence.*

### Agent 4's Decision Space & State Machine:
*   **Trigger Evaluation:** Agent 4 continuously monitors the local SQLite database. It calculates if a sufficient "batch" of highly confident new cases (e.g., 10-20 completed encounters) has accumulated to justify a training epoch.
*   **Resource Monitoring:** Before initiating training, the agent checks the thermal state and CPU load of the Raspberry Pi 4. If the gateway is currently handling a live ASHA query (Agents 1-3 active), Agent 4 yields priority, queuing the training task to ensure zero latency impact on live triage.
*   **Connectivity Polling:** Agent 4 acts as a Delay-Tolerant Networking (DTN) manager. It polls the upstream cloud connection. If the connection is dead, it safely stores the quantized gradient updates with a cryptographic timestamp, waiting for the optimal transmission window (usually overnight).

***

## 3. End-to-End FL Lifecycle: The 6-Step Agentic Flow

The complete flow from local patient interaction to global model optimization follows a strict 6-step lifecycle.

### Step 1: Local Data Ingestion & Pseudo-Labeling
As ASHA workers interact with patients via their Android phones (Layer 3), offline case data is generated. When the ASHA returns to the PHC or connects to the local Wi-Fi, the phone silently syncs these records to the PHC Gateway (Layer 4). 
Agent 4 ingests these records. Because actual ground-truth outcomes (e.g., whether the patient actually had pneumonia) might only be confirmed days later via hospital feedback, Agent 4 utilizes **pseudo-labeling**. It pairs the initial ASHA input features with the highest-confidence outputs from the RAG Diagnosis Agent, effectively preparing a localized training dataset representing the PHC's specific demographic baseline.

### Step 2: On-Device Model Fine-Tuning
Once the batch threshold is met and compute resources are free, Agent 4 initiates local training using a lightweight framework (e.g., Flower). 
*   The target of the fine-tuning is the underlying pre-triage classifier (which detects danger signs) and the retrieval cross-encoder weights.
*   The agent runs Stochastic Gradient Descent (SGD) for a set number of local epochs (usually 3 to 5).
*   During this phase, the model learns the statistical distribution of the local village's health patterns (e.g., an anomalous spike in respiratory illnesses during harvest season).

### Step 3: Differential Privacy Injection (Local Phase)
Before any weight update is allowed to leave the PHC Gateway, Agent 4 applies a rigorous Differential Privacy (DP) transformation to mathematically guarantee that no single patient's data can be reverse-engineered from the model updates.
1.  **Gradient Clipping:** The agent calculates the L2-norm of the generated gradients. If the norm exceeds a pre-defined threshold factor, it is mathematically scaled down. This ensures that a single extreme outlier case cannot heavily skew the update vector.
2.  **Gaussian Noise Addition:** The agent injects calibrated Gaussian noise into the clipped gradients. The variance of this noise is strictly controlled by the privacy budget parameters (Epsilon and Delta). AyushBot is tuned to maintain a stringent privacy budget, preventing model-inversion attacks.

### Step 4: Asynchronous Store-and-Forward Transmission
Rural network links are ephemeral. Agent 4 quantizes the privatized gradient vector from a 32-bit float matrix down to an 8-bit or ternary representation, aggressively compressing the payload from megabytes to kilobytes.
*   The agent wraps this payload in an ASCON-128 encrypted MQTT/QUIC packet.
*   If the cloud is unreachable, the packet enters a durable queue (Store-and-Forward).
*   When a stable connection is detected (e.g., 2:00 AM via a weak 3G signal), Agent 4 negotiates a TLS 1.3 handshake and transmits the payload to the Layer 5 Cloud Aggregator.

### Step 5: Global Aggregation & Non-IID Compensation (Cloud Phase)
At the cloud layer, the FL Server receives asynchronous updates from hundreds of PHC Gateways across different districts. Standard Federated Averaging (FedAvg) fails here because the data is Non-IID (Independent and Identically Distributed). To prevent the global model from forgetting one district's diseases while learning another's, the cloud server employs advanced aggregation:
*   **FedProx / SCAFFOLD Algorithm:** The server uses proximal regularization. It limits how far local updates can diverge from the global baseline. This ensures that a model learning about malaria in coastal regions doesn't catastrophically forget how to diagnose malnutrition in arid regions.
*   **Byzantine Fault Tolerance (Krum):** The server analyzes incoming gradient vectors in a high-dimensional space. If a specific PHC Gateway's update is a statistical anomaly (perhaps due to a faulty sensor pack consistently reading wrong oxygen levels, or a compromised node), the Krum aggregator mathematically isolates and rejects the poisoned gradient, preserving global model integrity.

### Step 6: Global Model Distribution & Edge Rollout
Once the cloud server successfully aggregates a new global model generation, the lifecycle closes. 
*   The cloud pushes the compressed delta (the difference between the old and new model) back down to the PHC Gateways.
*   Agent 4 receives the delta, verifies its cryptographic signature, applies the update to the local instance, and quietly hot-swaps the active model weights in memory without interrupting ongoing ASHA queries. 

***

## 4. Technical Grounding: Addressing Statistical & Network Bottlenecks

### The Straggler Problem
In rural deployments, some PHC Gateways will lose power or connectivity for days. The FL architecture handles this through **Asynchronous Federated Optimization**. The cloud aggregator does not wait for all nodes to report back (which would freeze the whole system). Instead, it operates on a dynamic buffer. If a gateway comes back online after a week, its "stale" gradient update is heavily discounted by a temporal decay factor, allowing it to contribute without reverting the progress of the global model.

### Hardware Constraints & TinyML Integration
While the heavy FL computation happens on the Raspberry Pi 4 (Layer 4), the TinyML models residing on the Arduino Sensor Packs (Layer 2) are also updated via this pipeline. When the global model derives improved thresholds for detecting low oxygen saturation based on multi-district learning, Agent 4 compiles these new thresholds into a TinyML-compatible INT8 binary, and flashes it to the Arduino over BLE the next time the ASHA connects their phone to the sensor pack.

***

## 5. Coursework Mapping & Academic Relevance

This FL architecture serves as a masterclass implementation of the four core computer science curricula:

1.  **Computer Networks:** The entirely of the Agent 4 sync mechanism is a real-world implementation of **Delay-Tolerant Networking (DTN)**, Store-and-Forward routing, TLS 1.3 secure tunneling, and bandwidth-constrained TCP congestion control.
2.  **Design and Analysis of Algorithms:** The cloud aggregation phase relies on **High-Dimensional Geometry and Greedy Algorithms** (like Krum for Byzantine tolerance) to find the geometric median of gradient vectors in vector space. 
3.  **Discrete Mathematical Structures:** The application of **Differential Privacy** is deeply rooted in probability theory and discrete math, specifically analyzing Laplace and Gaussian noise distributions to guarantee mathematical bounds on data leakage.
4.  **Internet of Things (IoT):** The cascading update from Cloud $\rightarrow$ PHC Gateway (RPi4) $\rightarrow$ ASHA Phone (Android) $\rightarrow$ Sensor Pack (Arduino) represents a flawless top-to-bottom edge-IoT ecosystem management pipeline.

## 6. Conclusion

The AyushBot Federated Learning architecture transcends basic API-wrapper designs by engineering a robust, mathematically secure, and network-resilient intelligence loop. By utilizing an autonomous agent (Agent 4) to abstract away the complexities of privacy injection, non-IID data distribution, and ephemeral connectivity, the system ensures that every patient interaction in the most remote village incrementally improves the diagnostic accuracy of the entire national network—all without a single raw medical record ever leaving the local clinic.