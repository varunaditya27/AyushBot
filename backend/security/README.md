# Authentication And Transport Security

AyushBot uses database-backed local identities, Argon2id password hashes via
`argon2-cffi`, and ES256 JWT access/refresh tokens. Passwords shorter than 12
characters are rejected before hashing. Access and refresh JWT identifiers are
stored only as SHA-256 hashes.

## Token Behavior

- Access tokens include `iss`, `aud`, `sub`, `role`, `device_id`, `kid`, `jti`,
  `iat`, `nbf`, `exp`, and token type.
- Every access request verifies the signature and checks the token record,
  account, and provisioned device status.
- Refresh tokens are single-use. Reuse revokes the complete token family and
  creates a security audit event.
- Logout revokes the complete family.
- Old public keys may remain configured during rotation; only `active_kid`
  signs new tokens.

## Required Manual Setup

Create the ES256 files outside the repository and install them at:

```text
infra/certs/jwt_gateway_2026_01_private.pem
infra/certs/jwt_gateway_2026_01_public.pem
```

Commands are documented in [infra/certs/README.md](../../infra/certs/README.md).
Then populate the `auth.keys` section in `backend/config.yaml`.

Migrate and create the first administrator interactively:

```bash
make migrate-db
make bootstrap-admin
```

The password is read with `getpass`; it is not passed on the command line or
written to configuration. The MedicalOfficer logs in through
`POST /api/v1/auth/login` and provisions each tablet through
`POST /api/v1/auth/provision/tablet`.

## Production Startup

Set `environment: production`, explicit CORS origins, JWT key paths, API TLS
paths, and MQTT mTLS paths. Startup fails when any required file is missing.
JWT keys must be readable ES256/P-256 PEM files, and the active private key must
match its public key.

Run the API with its installed certificate and key:

```bash
.venv/bin/uvicorn backend.api.main:app \
  --host 0.0.0.0 --port 8443 \
  --ssl-certfile infra/certs/api_server.crt \
  --ssl-keyfile infra/certs/api_server.key
```

Use `infra/mosquitto/mosquitto.conf` and `infra/mosquitto/acl.conf` for the
TLS-only broker. Tablet certificate common names must equal provisioned device
IDs.
