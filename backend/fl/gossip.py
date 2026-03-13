# =============================================================================
# AyushBot Backend — FL Gossip Protocol (Peer-to-Peer Gradient Sharing)
# =============================================================================
#
# PURPOSE:
#   Implements an optional peer-to-peer gradient exchange protocol between
#   nearby PHC gateways. When the cloud FL server is unreachable, gateways
#   within the same district can share DP-protected gradients over a local
#   mesh network, enabling decentralized model improvement.
#
# WHY GOSSIP:
#   In extremely remote areas, cloud connectivity may be unavailable for
#   weeks. If two PHC gateways are within local network range (e.g., same
#   LAN at a district office, or ad-hoc Wi-Fi during field visits), gossip
#   allows them to benefit from each other's training data without needing
#   the central FL server.
#
# PROTOCOL:
#   Based on a simplified Gossip Learning protocol:
#
#   1. DISCOVERY: Gateways broadcast a periodic mDNS/Bonjour announcement
#      on the local network: "I am an AyushBot gateway at [IP], model
#      version [V], with [N] buffered gradients."
#
#   2. HANDSHAKE: When two gateways discover each other:
#      a. Mutual TLS authentication using device certificates
#      b. Exchange model version compatibility check
#      c. If compatible → proceed to gradient exchange
#
#   3. EXCHANGE: Each gateway sends its latest DP-protected gradient to the
#      other. Both gateways apply the received gradient to their local model
#      using a weighted average:
#        new_weights = (1-α) * local_weights + α * received_gradient
#      where α is a mixing coefficient (default: 0.3, configurable).
#
#   4. PROTOCOL SAFEGUARDS:
#      - Only DP-protected gradients are shared (full dataset never leaves)
#      - Rate-limited to max 1 exchange per gateway pair per 24 hours
#      - Byzantine tolerance: A gateway only accepts gradients from
#        authenticated peers with valid device certificates
#
# LIMITATIONS:
#   - Less converge-efficient than centralized FL (FedAvg)
#   - No global coordination: model versions may drift between gateways
#   - Designed as a resilience mechanism, not a replacement for cloud FL
#
# CONFIGURATION (config.yaml):
#   - gossip_enabled: bool (default: false; opt-in feature)
#   - gossip_port: int (default: 5353 for mDNS)
#   - gossip_mixing_alpha: float (default: 0.3)
#   - gossip_max_exchanges_per_day: int (default: 1)
#
# INPUTS:
#   - Local DP-protected gradient (from aggregator.py)
#   - List of discovered peer gateways
#
# OUTPUTS:
#   - Updated local model weights (if gossip exchange occurred)
#   - Gossip log: peer_id, timestamp, gradient_exchanged, mixing_applied
# =============================================================================
