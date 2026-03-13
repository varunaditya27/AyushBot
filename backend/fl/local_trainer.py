# =============================================================================
# AyushBot Backend — FL Local Trainer (On-Device Fine-Tuning)
# =============================================================================
#
# PURPOSE:
#   Performs on-device fine-tuning of the local triage XGBoost model using
#   accumulated clinical encounter data. This runs on the PHC gateway
#   (Raspberry Pi 4) as a background process, managed by Agent 4 (FL Sync).
#
# TRAINING DATA SOURCE:
#   When an ASHA completes a patient assessment, the encounter record is
#   stored in the local SQLite database. Over time, these records accumulate.
#   The local trainer reads completed encounter records and uses them to
#   fine-tune the pre-trained XGBoost model's weights.
#
# PSEUDO-LABELING STRATEGY:
#   Ground-truth outcomes (confirmed doctor diagnosis) may take days to arrive.
#   Until then, the trainer uses pseudo-labels:
#     - Label = Agent 2's highest-confidence diagnosis + Agent 1's risk level
#     - Only high-confidence cases (model confidence > 0.8) are used for
#       training to avoid reinforcing errors
#     - When a confirmed outcome eventually arrives (from the PHC doctor's
#       feedback), the pseudo-label is replaced with the ground truth and
#       the sample is re-weighted for the next training round
#
# TRAINING PROCEDURE:
#   1. Query the local DB for the latest batch of completed encounters
#   2. Extract the feature vectors (same features as Agent 1's input)
#   3. Extract pseudo-labels (or ground truth if available)
#   4. Fine-tune the XGBoost model using incremental learning:
#      - SGD with learning rate 0.01
#      - 3-5 local epochs
#      - Batch size limited by available training data (typically 10-50 samples)
#   5. Compute the gradient (delta between new weights and old weights)
#   6. Pass the gradient to dp_mechanism.py for privacy protection
#
# RESOURCE CONSTRAINTS:
#   - Training happens ONLY when no live triage is running (Agent 4's guard)
#   - CPU: max 2 of 4 cores on RPi 4
#   - Memory: < 1 GB peak usage
#   - Duration: typically 1-5 minutes per round
#
# INPUTS:
#   - SQLite encounter records (features + labels)
#   - Current model weights (from backend/models/ or a configured path)
#   - Training config: epochs, learning_rate, min_batch_size
#
# OUTPUTS:
#   - Updated local model weights (saved to disk)
#   - Raw gradient vector (new_weights - old_weights), passed to dp_mechanism
#   - Training log: epochs completed, loss history, samples used
# =============================================================================
