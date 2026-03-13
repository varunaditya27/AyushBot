# =============================================================================
# AyushBot Infrastructure — TLS Certificate Generation Script
# =============================================================================
#
# PURPOSE:
#   Generates a self-signed PKI (Public Key Infrastructure) for development
#   and initial deployment of the AyushBot system. Creates a CA (Certificate
#   Authority) and issues server/client certificates for:
#     - Mosquitto MQTT broker (server cert + client certs)
#     - Flower FL gRPC connections (mTLS between gateway and cloud)
#     - Backend HTTPS (optional, for direct API access)
#
# CERTIFICATES GENERATED:
#
#   1. Certificate Authority (CA)
#      - ca.key (CA private key — GUARD THIS CAREFULLY)
#      - ca.crt (CA certificate — distributed to all clients)
#      - Validity: 10 years
#      - Used to sign all server and client certificates
#
#   2. MQTT Server Certificate
#      - mqtt_server.key (private key for Mosquitto broker)
#      - mqtt_server.crt (server cert, signed by CA)
#      - CN: hostname of the RPi 4 gateway
#      - SAN: IP address of the RPi 4 on the local network
#
#   3. MQTT Client Certificates
#      - android_client.key + android_client.crt (for Android phone)
#      - backend_client.key + backend_client.crt (for backend services)
#      - Used for mutual TLS authentication (mTLS)
#
#   4. FL gRPC Certificates
#      - fl_server.key + fl_server.crt (for cloud FL server)
#      - fl_client.key + fl_client.crt (for gateway FL client)
#      - Required for Flower gRPC with TLS enabled
#
# ALGORITHM:
#   - RSA 4096-bit keys (secure, widely compatible)
#   - SHA-256 signatures
#   - Certificate validity: 1 year (rotate annually)
#
# OUTPUT DIRECTORY:
#   All generated certificates are placed in infra/certs/
#   This directory is in .gitignore — NEVER commit private keys to Git.
#
# PRODUCTION NOTE:
#   For production deployment, replace these self-signed certificates with
#   certificates issued by a proper CA (e.g., Let's Encrypt for public-facing
#   services, or an organizational internal CA for private infrastructure).
#
# USAGE:
#   chmod +x infra/certs/generate_certs.sh
#   ./infra/certs/generate_certs.sh
# =============================================================================
