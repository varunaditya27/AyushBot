# =============================================================================
# AyushBot Backend — Agent 4: FL Participation & Sync Agent (Background Learner)
# =============================================================================
#
# PURPOSE:
#   This agent runs asynchronously in the background on the PHC gateway
#   (Raspberry Pi 4). It is NOT part of the real-time triage pipeline —
#   it operates independently to continuously improve the local triage
#   model using privacy-preserving federated learning.
#
#   Its mandate: Optimize the local model based on accumulated clinical data,
#   protect patient privacy with differential privacy, and navigate network
#   instability to contribute gradient updates to the global model.
#
# TRIGGER CONDITIONS:
#   Agent 4 does NOT activate on every patient visit. It monitors the local
#   SQLite database and triggers training when ALL of these conditions are met:
#     1. A sufficient batch of high-confidence cases has accumulated
#        (configurable threshold, default: 10-20 completed encounters)
#     2. The gateway CPU load is low (Agents 1-3 are not actively processing
#        a live ASHA query — FL training must NEVER impact real-time triage)
#     3. The gateway thermal state is acceptable (RPi 4 throttles under heat)
#
# STATE MACHINE:
#   Agent 4 has its own internal state machine with the following states:
#     IDLE → COLLECTING → READY_TO_TRAIN → TRAINING → DP_INJECTION →
#     AWAITING_SYNC → SYNCING → IDLE
#
#   State transitions:
#     - IDLE → COLLECTING: New cases arrive from ASHA phone sync
#     - COLLECTING → READY_TO_TRAIN: Batch threshold reached
#     - READY_TO_TRAIN → TRAINING: CPU is free, thermal OK
#     - TRAINING → DP_INJECTION: Local SGD complete (5 epochs)
#     - DP_INJECTION → AWAITING_SYNC: Gradients clipped + noise added
#     - AWAITING_SYNC → SYNCING: Internet connection detected
#     - SYNCING → IDLE: Gradient upload successful (or stored locally if offline)
#
# PROCESSING STEPS:
#
#   Step 1 — Local Data Ingestion & Pseudo-Labeling
#     When ASHA phones sync completed case records to the gateway, Agent 4
#     ingests them. Because ground-truth outcomes (actual diagnosis confirmed
#     by a doctor) may take days, Agent 4 uses pseudo-labeling: it pairs
#     the raw vitals/features with the highest-confidence outputs from Agent 2
#     (the RAG Diagnosis Agent) as weak supervision labels.
#
#   Step 2 — On-Device Model Fine-Tuning
#     Using the Flower FL client library:
#     - Target model: The XGBoost pre-triage classifier (Agent 1's model)
#     - Training: Stochastic Gradient Descent for 3-5 local epochs
#     - The model learns the statistical distribution of this PHC's specific
#       local health patterns (e.g., respiratory illness spike during harvest)
#
#   Step 3 — Differential Privacy Injection
#     BEFORE any gradient leaves the device:
#     a. Gradient Clipping: Compute the L2 norm of the gradient vector.
#        If it exceeds the clipping threshold (default: 1.0), scale it down.
#        This prevents any single extreme case from dominating the update.
#     b. Gaussian Noise Addition: Inject calibrated Gaussian noise with
#        variance controlled by the privacy budget (ε=1.0, δ=10^-6).
#        This mathematically guarantees that no single patient's data can
#        be reverse-engineered from the gradient update.
#
#   Step 4 — DTN-Style Synchronization
#     Agent 4 polls the upstream cloud connection:
#     - If online: Upload the DP-injected gradient to the Flower FL server
#       via QUIC transport (encrypted, reliable)
#     - If offline: Store the gradient update locally with a cryptographic
#       timestamp. Queue it for upload at the next connectivity window
#       (typically overnight). This is Delay-Tolerant Networking (DTN).
#     - If the store queue has updates older than 7 days, flag for manual
#       sync (ASHA or Medical Officer can physically carry to connected PHC).
#
# RESOURCE MANAGEMENT:
#   - Training runs at LOW priority (nice +10 on Linux)
#   - Maximum 2 CPU cores allocated (out of 4 on RPi 4)
#   - Training aborted if live triage request arrives (yield immediately)
#   - Memory budget: < 1 GB for training (leaves room for RAG + LLM)
#
# OUTPUTS:
#   - Updated local model weights (written to disk)
#   - Gradient update file (for cloud sync)
#   - Training log: epochs, loss, accuracy, DP parameters, sync status
#
# LATENCY: Not real-time. Training typically takes 5-30 minutes per round.
# =============================================================================
