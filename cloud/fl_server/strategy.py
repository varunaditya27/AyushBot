# =============================================================================
# AyushBot Cloud — FL Aggregation Strategies
# =============================================================================
#
# PURPOSE:
#   Defines the federated aggregation strategies that the FL server uses to
#   combine DP-protected gradient updates from multiple PHC gateways into
#   a single global model update.
#
# STRATEGIES IMPLEMENTED:
#
#   1. FedAvg (Federated Averaging)
#      The baseline strategy. Computes a weighted average of client gradients:
#        global_gradient = Σ (n_k / N) * gradient_k
#      where n_k = samples used by client k, N = total samples across all clients.
#      Pros: Simple, well-understood, low communication overhead.
#      Cons: Converges slowly with non-IID data (different PHCs see different
#             disease distributions — e.g., malaria-heavy vs. respiratory-heavy).
#
#   2. FedProx (Federated Proximal)
#      FedAvg + a proximal regularization term that penalizes local models
#      for drifting too far from the global model:
#        local_objective = loss + (μ/2) * ||w_local - w_global||²
#      This improves convergence when PHC data is highly heterogeneous.
#      The proximal coefficient μ (default: 0.01) controls the regularization
#      strength.
#
#   3. SCAFFOLD (Stochastic Controlled Averaging)
#      Uses control variates to correct for client drift in non-IID settings.
#      Each client maintains a control variate that estimates the difference
#      between the local gradient and the global gradient. The server also
#      maintains a global control variate.
#      Pros: Fastest convergence for non-IID data.
#      Cons: 2x communication cost (sends gradients + control variates).
#
# BYZANTINE DEFENSE (Optional):
#   Can be composed with any strategy above:
#
#   - Trimmed Mean: Discard the top and bottom β% of gradient values per
#     dimension before averaging. Protects against extreme outliers.
#
#   - Multi-Krum: Score each client's gradient by its distance to the
#     nearest k other clients. Select the f most "central" gradients for
#     aggregation. Robust to up to f Byzantine (malicious/corrupted) clients.
#
# STRATEGY SELECTION:
#   Configured in the FL server's config. Recommended progression:
#   - Phase 1 (initial deployment): FedAvg (simplest, hardest to misconfigure)
#   - Phase 2 (regional rollout): FedProx (handles inter-PHC data heterogeneity)
#   - Phase 3 (national scale): SCAFFOLD (optimal convergence at scale)
#
# INTERFACE:
#   Each strategy implements Flower's Strategy abstract class:
#     - aggregate_fit(results) → aggregated_weights
#     - aggregate_evaluate(results) → aggregated_metrics
#     - configure_fit(config) → per-client config overrides
# =============================================================================
