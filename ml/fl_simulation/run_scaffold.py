# =============================================================================
# AyushBot ML — FL Simulation: Run SCAFFOLD Experiment
# =============================================================================
#
# PURPOSE:
#   Runs a SCAFFOLD (Stochastic Controlled Averaging for Federated Learning)
#   simulation. SCAFFOLD uses control variates to correct for client drift
#   and theoretically achieves faster convergence than FedAvg/FedProx on
#   non-IID data.
#
# SCAFFOLD MECHANISM:
#   Each client maintains a control variate c_k that estimates the difference
#   between the local gradient and the global gradient. During training:
#     - Client update: w_k = w - η * (∇F_k(w) - c_k + c_global)
#     - Control variate update: c_k_new = c_k - c_global + (1/Kη)(w_global - w_k)
#   The server aggregates both model updates AND control variates.
#
# TRADE-OFF:
#   SCAFFOLD requires 2x communication per round (model + control variates)
#   but converges in fewer rounds. Net benefit depends on whether rounds
#   or bandwidth is the bottleneck (for rural India, rounds are bottleneck).
#
# EXPERIMENT:
#   - Same node setup as previous experiments
#   - Compare: FedAvg vs FedProx(best μ) vs SCAFFOLD
#   - Measure: rounds to target accuracy, total communication cost
#
# OUTPUT:
#   - Convergence curves: ml/fl_simulation/results/scaffold_convergence.csv
#   - Three-way comparison plot: FedAvg vs FedProx vs SCAFFOLD
#   - Communication efficiency analysis
# =============================================================================
