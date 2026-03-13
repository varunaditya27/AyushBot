# =============================================================================
# AyushBot Backend — FL Differential Privacy Mechanism
# =============================================================================
#
# PURPOSE:
#   Implements the differential privacy (DP) guarantees that protect patient
#   data before any gradient update leaves the PHC gateway. This is the
#   mathematical backbone of AyushBot's privacy-preserving FL system.
#
# WHY DIFFERENTIAL PRIVACY:
#   Gradient updates from on-device training can leak information about the
#   training data. A sufficiently motivated adversary could potentially
#   reconstruct patient attributes from raw gradients (gradient inversion
#   attacks). DP provides a mathematical guarantee that this is infeasible.
#
# DP MECHANISM: Gaussian Mechanism with Gradient Clipping
#
#   Step 1 — Per-Sample Gradient Clipping
#     For each training sample's individual gradient contribution:
#       g_clipped = g * min(1, C / ||g||_2)
#     where:
#       C = clipping threshold (default: 1.0)
#       ||g||_2 = L2 norm of the gradient vector
#     This bounds the maximum influence of any single patient's data on the
#     total gradient. A patient with an extreme or rare condition cannot
#     disproportionately influence the gradient.
#
#   Step 2 — Gaussian Noise Addition
#     After clipping, add calibrated Gaussian noise to the aggregated gradient:
#       g_private = g_clipped + N(0, σ²I)
#     where:
#       σ = C * sqrt(2 * ln(1.25/δ)) / ε
#       ε = privacy budget (default: 1.0 — strong privacy)
#       δ = failure probability (default: 10^-6)
#     This noise calibration follows the standard Gaussian mechanism from
#     Dwork & Roth's "The Algorithmic Foundations of Differential Privacy."
#
# PRIVACY BUDGET TRACKING:
#   Each training round consumes a portion of the privacy budget (ε).
#   The mechanism maintains a running account of cumulative privacy loss
#   using Rényi Differential Privacy (RDP) composition:
#     - After each round, compute the RDP guarantee at multiple α values
#     - Convert to (ε, δ)-DP using RDP-to-DP conversion
#     - If the cumulative ε exceeds the configured maximum (e.g., 8.0),
#       STOP TRAINING. No more gradient updates are allowed until the
#       privacy budget resets (typically per-quarter).
#   This prevents privacy degradation from repeated training rounds.
#
# PRIVACY PARAMETERS (configurable in config.yaml):
#   - epsilon: float (default: 1.0, per-round privacy budget)
#   - delta: float (default: 1e-6, failure probability)
#   - max_grad_norm: float (default: 1.0, clipping threshold C)
#   - noise_multiplier: float (derived from ε, δ, C; can also be set directly)
#   - max_cumulative_epsilon: float (default: 8.0, lifetime budget)
#
# INPUTS:
#   - Raw gradient vector from local_trainer.py
#   - DP configuration parameters
#   - Current cumulative privacy budget consumption
#
# OUTPUTS:
#   - Privacy-protected gradient vector (clipped + noised)
#   - Updated cumulative privacy budget
#   - DP audit log: ε_spent, σ_used, gradient_norm_before_clipping
# =============================================================================
