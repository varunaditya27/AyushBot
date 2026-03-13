# =============================================================================
# AyushBot Tests — Unit: Differential Privacy Mechanism
# =============================================================================
#
# PURPOSE:
#   Unit tests for the DP (Differential Privacy) module used in federated
#   learning (backend/fl/dp_mechanism.py). Verifies that gradient clipping
#   and noise addition conform to the configured privacy budget.
#
# TEST CASES:
#
#   test_gradient_clipping_max_norm
#     Input: A gradient vector with L2 norm = 10.0, max_norm = 1.0
#     Expected: Output gradient has L2 norm exactly 1.0 (clipped)
#     Verify: Direction is preserved (unit vector matches original direction)
#
#   test_gradient_clipping_no_effect_below_threshold
#     Input: A gradient vector with L2 norm = 0.5, max_norm = 1.0
#     Expected: Output gradient is identical to input (no clipping needed)
#
#   test_gaussian_noise_addition
#     Input: A clipped gradient, sigma = 0.1
#     Expected: Output = clipped_gradient + noise, where noise ~ N(0, σ²I)
#     Statistical test: Over 1000 trials, the noise mean ≈ 0 and
#       noise std ≈ sigma (within statistical tolerance)
#
#   test_privacy_budget_accounting
#     Input: Run K rounds of gradient uploads with ε=1.0, δ=10^-6
#     Expected: The cumulative privacy budget (tracked by a privacy
#       accountant, e.g., RDP or Moments Accountant) does not exceed
#       the configured total budget
#
#   test_dp_does_not_leak_original_gradient
#     Statistical test: Given two different input gradients (differing by
#     one sample), verify that the distributions of noised outputs are
#     statistically indistinguishable (within ε tolerance).
#     This is the core DP guarantee.
#
#   test_noise_scale_increases_with_sensitivity
#     Input: Same ε, δ but different max_norm (sensitivity) values
#     Expected: Higher max_norm → larger noise sigma (more noise needed
#       to protect more sensitive gradients)
#
#   test_dp_with_zero_epsilon
#     Input: ε = 0 (infinite privacy)
#     Expected: Output is pure noise (original gradient fully obscured)
#     This verifies the DP mechanism's behavior at the privacy extreme.
#
# FIXTURES USED:
#   - test_config (with configured DP parameters)
# =============================================================================
