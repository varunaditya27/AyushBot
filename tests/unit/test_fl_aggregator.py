# =============================================================================
# AyushBot Tests — Unit: FL Aggregator
# =============================================================================
#
# PURPOSE:
#   Unit tests for the federated learning aggregation logic
#   (backend/fl/aggregator.py). Verifies that gradient aggregation
#   strategies produce correct results.
#
# TEST CASES:
#
#   test_fedavg_weighted_average
#     Input: 3 client gradients with sample counts [100, 200, 300]
#     Expected: Aggregated gradient = weighted average by sample count
#     Verify: sum(w_i * g_i) / sum(w_i) computed correctly
#
#   test_fedavg_single_client
#     Input: 1 client gradient
#     Expected: Aggregated gradient equals the single client's gradient
#
#   test_fedprox_regularization_applied
#     Input: Client gradient that has drifted far from global model
#     Expected: FedProx pulls the aggregation closer to the global model
#       compared to FedAvg (proximal term effect)
#
#   test_byzantine_gradient_rejection
#     Input: 5 normal gradients + 1 gradient with L2 norm 100x larger
#     Expected: The Byzantine gradient is detected and excluded from
#       aggregation (norm clipping or Multi-Krum defense)
#
#   test_aggregation_with_nan_gradient
#     Input: 4 normal gradients + 1 gradient containing NaN values
#     Expected: NaN gradient is rejected, aggregation uses remaining 4
#
#   test_aggregation_preserves_model_shape
#     Input: Gradients with a specific tensor shape
#     Expected: Aggregated gradient has the same shape
#
# FIXTURES USED:
#   - test_config
# =============================================================================
