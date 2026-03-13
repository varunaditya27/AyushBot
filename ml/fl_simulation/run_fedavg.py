# =============================================================================
# AyushBot ML — FL Simulation: Run FedAvg Experiment
# =============================================================================
#
# PURPOSE:
#   Runs a complete Federated Averaging (FedAvg) simulation using the
#   synthetic PHC nodes from simulate_nodes.py. Measures convergence speed,
#   final accuracy, and communication cost.
#
# EXPERIMENT SETUP:
#   - Load simulated node data partitions
#   - Initialize a global XGBoost model (from 04_train_xgboost.py output)
#   - Run FL for T rounds (default: 50)
#   - In each round:
#     a. Select C% of available clients (default: C=30%, i.e., 6 of 20 nodes)
#     b. Each selected client performs local training (3-5 epochs)
#     c. Clients upload gradient updates (with DP noise)
#     d. Server computes weighted average of gradients
#     e. Apply aggregated gradient to global model
#     f. Evaluate global model on a centralized test set
#
# METRICS LOGGED PER ROUND:
#   - Global model accuracy, macro-F1, CRITICAL recall
#   - Per-client: local loss, gradient norm, samples used
#   - Communication: total bytes transferred
#   - Wall-clock time (simulated)
#
# COMPARISON BASELINES:
#   - Centralized training (upper bound): train on all data combined
#   - Local-only training (lower bound): each node trains independently
#   - FedAvg should converge between these bounds
#
# OUTPUT:
#   - Convergence curves: ml/fl_simulation/results/fedavg_convergence.csv
#   - Plots: accuracy vs. round, F1 vs. round, communication cost vs. round
#   - Final model: ml/fl_simulation/results/fedavg_global_model.json
# =============================================================================
