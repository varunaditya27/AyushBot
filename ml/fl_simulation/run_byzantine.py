# =============================================================================
# AyushBot ML — FL Simulation: Byzantine Robustness Experiment
# =============================================================================
#
# PURPOSE:
#   Tests the FL system's resilience to Byzantine (malicious or corrupted)
#   gradient updates from compromised or faulty PHC gateways.
#
# THREAT MODEL:
#   In a real deployment, some gateways might submit corrupted gradients due to:
#     - Hardware failure (faulty RPi 4 producing NaN/Inf gradients)
#     - Software bugs (incorrect feature engineering producing bad training data)
#     - Intentional manipulation (unlikely but must be considered)
#
# ATTACK TYPES SIMULATED:
#   1. Random noise injection: Byzantine nodes send random gradients
#   2. Sign-flip attack: Byzantine nodes flip the sign of their gradient
#   3. Label-flip attack: Byzantine nodes train on intentionally mislabeled data
#
# DEFENSE MECHANISMS TESTED:
#   1. No defense (baseline FedAvg): How badly does accuracy degrade?
#   2. Norm clipping: Reject gradients with L2 norm > threshold
#   3. Trimmed Mean: Discard top/bottom β% of gradient values per dimension
#   4. Multi-Krum: Select the most "central" gradients for aggregation
#
# EXPERIMENT MATRIX:
#   For each (attack_type × defense × num_byzantine_nodes):
#     - Run FL for T rounds
#     - Measure final global model accuracy and CRITICAL recall
#     - Compare with non-Byzantine baseline
#
# OUTPUT:
#   - Results table: ml/fl_simulation/results/byzantine_robustness.csv
#   - Heatmap plots: accuracy degradation vs. Byzantine fraction
#   - Recommendation: which defense to use in production
# =============================================================================
