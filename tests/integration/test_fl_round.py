# =============================================================================
# AyushBot Tests — Integration: Federated Learning Round
# =============================================================================
#
# PURPOSE:
#   Integration test for a complete FL training round:
#   Gateway local training → Gradient upload → Server aggregation → Model update
#   Verifies that the FL pipeline works end-to-end with DP and aggregation.
#
# TEST CASES:
#
#   test_single_fl_round_completes
#     Setup: Initialize a mock FL server and 3 FL clients (each with
#       a small local dataset)
#     Action: Execute one complete FL round:
#       1. Server sends current global model to clients
#       2. Each client trains locally for 1 epoch
#       3. Each client applies DP noise to gradients
#       4. Clients upload gradients to server
#       5. Server aggregates using FedAvg
#       6. Server updates global model
#     Expected: Global model updated successfully, all steps complete
#       without errors
#
#   test_fl_round_improves_accuracy
#     Setup: Start with a weak global model (random initialization)
#     Action: Run 5 FL rounds with 3 clients
#     Expected: Global model accuracy on the test set improves monotonically
#       (or at least trends upward over 5 rounds)
#
#   test_dp_noise_applied_to_gradients
#     Action: Capture the gradients before and after DP processing
#     Expected: Gradients are modified (noise added), L2 norm is clipped,
#       and the privacy accountant increments the spent budget
#
#   test_client_dropout_handling
#     Setup: 5 clients selected for a round, but only 3 respond
#     Expected: Server aggregates from the 3 responding clients,
#       round completes successfully (fault-tolerant)
#
# FIXTURES USED:
#   - test_config, mock_xgboost_model
# =============================================================================
