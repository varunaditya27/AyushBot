# =============================================================================
# AyushBot ML — FL Simulation: Simulate Federated Nodes
# =============================================================================
#
# PURPOSE:
#   Creates synthetic PHC gateway nodes for federated learning experiments.
#   Since we cannot run experiments with real PHC gateways during development,
#   this script simulates N gateways, each with a distinct local data
#   distribution that mimics the data heterogeneity of real Indian PHCs.
#
# SIMULATION APPROACH:
#   1. Partition the training dataset into N non-overlapping shards
#   2. Apply non-IID distribution skew to simulate real-world heterogeneity:
#      - Dirichlet allocation (α parameter controls skew severity):
#        α = 0.1 → Highly non-IID (each PHC sees mostly 1-2 conditions)
#        α = 1.0 → Moderately non-IID (each PHC has a local specialty)
#        α = 100 → Nearly IID (uniform distribution, unrealistic)
#      - Geographic disease profiles:
#        Node 1: Malaria-heavy (simulating a tribal/forest area PHC)
#        Node 2: Respiratory-heavy (simulating a winter-prone hill PHC)
#        Node 3: Malnutrition-heavy (simulating a drought-prone area PHC)
#   3. Assign each node a connectivity profile:
#      - Always-on: 100% availability (urban PHC)
#      - Intermittent: 30-60% availability (semi-rural PHC)
#      - Rarely-on: 5-10% availability (remote tribal PHC)
#
# CONFIGURABLE PARAMETERS:
#   - num_nodes: int (default: 20, simulating 20 PHCs)
#   - samples_per_node: int (default: 50-200, realistic case count)
#   - dirichlet_alpha: float (default: 0.5, moderate non-IID)
#   - connectivity_distribution: dict mapping profile → percentage
#   - byzantine_nodes: int (default: 0, nodes sending corrupted gradients)
#
# OUTPUT:
#   - Directory: ml/fl_simulation/node_data/ (one CSV per simulated node)
#   - Node metadata: ml/fl_simulation/node_config.json
#   - Distribution visualization: ml/fl_simulation/data_distribution.png
# =============================================================================
