# =============================================================================
# AyushBot ML — FL Simulation: Gossip Protocol Experiment
# =============================================================================
#
# PURPOSE:
#   Simulates the peer-to-peer gossip gradient sharing protocol to evaluate
#   its effectiveness as a fallback when the central FL server is unreachable.
#
# SETUP:
#   - N simulated nodes in a geographic topology (graph where edges represent
#     physical proximity / network reachability)
#   - Central server has X% uptime (simulate intermittent cloud connectivity)
#   - When server is offline, neighboring nodes can gossip-share gradients
#
# EXPERIMENT:
#   Compare four scenarios:
#   1. Central FL only, 100% connectivity (upper bound)
#   2. Central FL only, 30% connectivity (realistic rural baseline)
#   3. Central FL + Gossip, 30% connectivity (proposed hybrid approach)
#   4. Gossip only, 0% central connectivity (extreme fallback)
#
# METRICS:
#   - Model accuracy convergence over time (wall-clock, not rounds)
#   - Staleness: average age of integrated gradients
#   - Model divergence: how much do individual node models differ?
#   - Communication cost: bytes transferred
#
# OUTPUT:
#   - Convergence comparison: ml/fl_simulation/results/gossip_comparison.csv
#   - Four-scenario overlay plot
#   - Recommendation for gossip_mixing_alpha parameter
# =============================================================================
