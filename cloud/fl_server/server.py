# =============================================================================
# AyushBot Cloud — FL Server Module
# =============================================================================
#
# PURPOSE:
#   Implements the central Flower FL server that aggregates DP-protected
#   gradient updates from PHC gateways across India and produces updated
#   global model weights.
#
# DEPLOYMENT:
#   Runs in the cloud (AWS/GCP/Azure) as a long-running service. This is
#   the ONLY cloud component — all clinical reasoning happens on-device.
#   The cloud's sole job is FL aggregation and administrative analytics.
#
# FLOWER SERVER ARCHITECTURE:
#   Uses Flower (flwr) as the FL orchestration framework:
#   - gRPC transport with TLS 1.3 + mTLS for gateway authentication
#   - Supports heterogeneous clients (different RPi 4 hardware configs)
#   - Configurable minimum number of clients per round (min_fit_clients)
#
# FL ROUND LIFECYCLE:
#
#   1. WAIT FOR CLIENTS
#      The server waits until at least min_fit_clients gateways have
#      connected and submitted gradient updates. This may take hours or
#      days in rural deployment where connectivity is intermittent.
#
#   2. AGGREGATION
#      Once enough gradients are collected, apply the configured aggregation
#      strategy (see strategy.py):
#        - FedAvg: Weighted average of gradients, proportional to sample count
#        - FedProx: FedAvg + proximal term (penalizes deviation from global model)
#        - SCAFFOLD: Variance-reduced aggregation for heterogeneous data
#      The strategy is configurable — start with FedAvg, upgrade as needed.
#
#   3. GLOBAL MODEL UPDATE
#      The aggregated gradient is applied to the global model weights.
#      The new global model is registered in the model registry (model_registry.py).
#
#   4. DISTRIBUTE
#      Push the updated global model weights to all connected gateways
#      via Flower's evaluate() callback. Gateways that are offline will
#      receive the update on their next sync connection.
#
# BYZANTINE RESILIENCE:
#   The server performs anomaly detection on incoming gradients:
#   - Gradient norm outlier detection (reject updates with norms > 3σ)
#   - Source authentication (verify HMAC signature from each gateway)
#   - Optionally: Trimmed Mean or Krum aggregation for Byzantine tolerance
#
# CONFIGURATION:
#   - min_fit_clients: int (default: 5, minimum gateways per round)
#   - min_available_clients: int (default: 3)
#   - aggregation_strategy: str (FedAvg | FedProx | SCAFFOLD)
#   - num_rounds: int (total FL rounds to run, or "continuous")
#   - server_address: str (bind address, e.g., "0.0.0.0:8080")
#   - tls_cert_path, tls_key_path, ca_cert_path: TLS configuration
#
# LOGGING:
#   Every FL round is logged with:
#   - round_id, num_clients, aggregation_strategy_used
#   - per-client: device_id, gradient_norm, sample_count, dp_params
#   - post-aggregation: global_loss, global_accuracy (on validation set)
# =============================================================================
