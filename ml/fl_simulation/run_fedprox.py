# =============================================================================
# AyushBot ML — FL Simulation: Run FedProx Experiment
# =============================================================================
#
# PURPOSE:
#   Runs a Federated Proximal (FedProx) simulation and compares convergence
#   with FedAvg on the same non-IID data partitions.
#
# DIFFERENCE FROM FedAvg:
#   FedProx adds a proximal regularization term to each client's local
#   objective function:
#     min_w { F_k(w) + (μ/2) * ||w - w_global||² }
#   where μ is the proximal coefficient.
#
#   This penalizes local models for drifting too far from the global model,
#   which is especially beneficial when data is highly non-IID.
#
# EXPERIMENT:
#   - Same setup as run_fedavg.py (same nodes, same partitions, same T rounds)
#   - Sweep over μ values: [0.001, 0.01, 0.1, 1.0]
#   - For each μ, log the same convergence metrics as FedAvg
#   - Generate a comparison plot: FedAvg vs. FedProx(μ=...) convergence
#
# OUTPUT:
#   - Convergence curves: ml/fl_simulation/results/fedprox_convergence_{mu}.csv
#   - Comparison plots: FedAvg vs FedProx convergence overlay
# =============================================================================
