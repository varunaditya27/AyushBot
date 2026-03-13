<div align="center">

# 🔒 Backend Security

**Zero-Trust Edge Authing & Identity Management**

</div>

## 📌 Overview

The `/backend/security` directory handles all authentication, authorization, and cryptographic operations for the PHC Gateway. Because the gateway broadcasts its own local WiFi network (WLAN) to the android tablets, it must restrict API and MQTT access strictly to provisioned ASHA devices to prevent rogue actors in the vicinity from intercepting offline telemetry.

## 🛡️ Security Posture

### JWT (JSON Web Tokens)
Instead of relying on username/password combos (which are difficult to manage offline), ASHA tablets are provisioned with long-lived ECDSA JWTs when first manufactured or deployed.
- **`auth.py`**: Interacts with the FastAPI dependency injection system (`Depends(get_current_asha)`). Decodes the JWT and validates the signature against the local `public_key.pem`.
- **RBAC**: Implements Role-Based Access Control. `AshaWorker` tokens can sync cases, but only `MedicalOfficer` tokens can access the `/api/v1/analytics` endpoints.

### Let's Encrypt / Local CA
To prevent Man-in-the-Middle (MITM) attacks on the local WLAN during MQTT synchronization:
- If an internet connection is available, the setup script requests a Let's Encrypt certificate.
- Otherwise, a self-signed Root CA is generated locally on the Pi and distributed to the Android tablets, ensuring secure `mqtts://` TLS 1.2+ encryption over the airgap.

## 🧩 Modularity

- **`jwt_handler.py`**: Encodes, decodes, and verifies cryptographic token expirations.
- **`hashing.py`**: Uses **Argon2** for password hashing (e.g., for the Medical Officer local dashboard login).
- **`device_fingerprint.py`**: Validates the MAC address and hardware UUID of connecting tablets to prevent token theft/replay attacks.

## 🔑 Key Management
The private keys (e.g., `private_key.pem`) used to sign the tokens are strictly managed by Docker secrets and are NEVER stored in this repository or the `/data` directory.
