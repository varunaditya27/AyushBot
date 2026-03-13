# =============================================================================
# AyushBot Backend — FL Sync Client (Cloud Communication via Flower)
# =============================================================================
#
# PURPOSE:
#   Handles the gateway-to-cloud communication for federated learning. This
#   module implements the Flower FL client that uploads DP-protected gradient
#   updates to the central FL server and downloads updated global model
#   weights.
#
# FLOWER FRAMEWORK:
#   AyushBot uses the Flower (flwr) open-source FL framework:
#   - The cloud runs the Flower FL server (see cloud/fl_server/server.py)
#   - Each PHC gateway runs a Flower FL client (this module)
#   - Communication uses gRPC over TLS 1.3 with mutual authentication
#
# SYNC WORKFLOW:
#
#   1. CONNECTION ATTEMPT
#      The sync client periodically attempts to connect to the cloud FL
#      server (configurable interval, default: every 6 hours):
#        - Check internet connectivity (ping cloud endpoint)
#        - If offline: log and retry at next interval
#        - If online: establish mTLS-authenticated gRPC connection
#
#   2. GRADIENT UPLOAD (fit round)
#      When the cloud server initiates a training round:
#        a. The client reads the latest gradient update from the local
#           aggregator's queue
#        b. Serializes the gradient + metadata (sample_count, dp_params)
#        c. Uploads to the server via Flower's fit() callback
#        d. Server acknowledges receipt; client marks the update as synced
#
#   3. MODEL DOWNLOAD (evaluate round)
#      After the server aggregates gradients from multiple gateways:
#        a. The server pushes the new global model weights to the client
#           via Flower's evaluate() callback
#        b. The client validates the received weights (size, shape, version)
#        c. Replaces the local model with the new global weights
#        d. Restarts Agent 1's XGBoost inference with the updated model
#
#   4. DTN FALLBACK
#      If the connection drops mid-transfer:
#        - Gradient upload: retry at next connectivity window (cached locally)
#        - Model download: continue using the existing local model until
#          the next successful sync
#
# AUTHENTICATION:
#   - mTLS: Each gateway has a unique client certificate signed by the
#     AyushBot CA (see infra/certs/). The server verifies the client cert
#     before accepting any gradient upload.
#   - Device ID: Each gradient carries the gateway's device ID (derived
#     from the client cert) for audit and provenance tracking.
#
# BANDWIDTH OPTIMIZATION:
#   - Gradients are compressed with zlib before upload (~70% reduction)
#   - Only gradient deltas are sent, not full model weights
#   - Server supports incremental sync (resume interrupted uploads)
#
# CONFIGURATION (config.yaml):
#   - fl_server_address: str (cloud FL server hostname:port)
#   - sync_interval_hours: int (default: 6)
#   - client_cert_path: str (path to gateway's client certificate)
#   - client_key_path: str (path to gateway's private key)
#   - ca_cert_path: str (path to CA certificate for server verification)
#
# INPUTS:
#   - Gradient update files from aggregator.py's queue
#   - Connection configuration from config.yaml
#
# OUTPUTS:
#   - Updated global model weights (written to disk)
#   - Sync log: timestamp, bytes_uploaded, bytes_downloaded, round_id, status
# =============================================================================
