# Required Certificates

Private keys and issued certificates are deployment inputs and are ignored by
Git. Do not run certificate-generation commands inside a source checkout used
for commits unless the output directory is already protected.

## Required Paths

Production configuration expects:

```text
infra/certs/ca.crt
infra/certs/api_server.crt
infra/certs/api_server.key
infra/certs/mqtt_server.crt
infra/certs/mqtt_server.key
infra/certs/backend_client.crt
infra/certs/backend_client.key
infra/certs/jwt_gateway_2026_01_public.pem
infra/certs/jwt_gateway_2026_01_private.pem
```

Each tablet also needs a unique client certificate and private key. Its
certificate common name must equal the provisioned `device_id`, because the
Mosquitto ACL uses the certificate identity as the MQTT username.

## ES256 JWT Key

Generate outside the repository, then install with restrictive permissions:

```bash
openssl ecparam -name prime256v1 -genkey -noout -out jwt_gateway_2026_01_private.pem
openssl ec -in jwt_gateway_2026_01_private.pem -pubout -out jwt_gateway_2026_01_public.pem
install -m 600 jwt_gateway_2026_01_private.pem /path/to/AyushBot/infra/certs/
install -m 644 jwt_gateway_2026_01_public.pem /path/to/AyushBot/infra/certs/
```

For rotation, add the new public/private pair under a new `kid`, make it
`auth.active_kid`, and retain the previous public key until all old access and
refresh tokens have expired.

## TLS Certificates

Use an organizational CA or approved local PHC CA. Server certificates must
include the gateway DNS name/IP in SAN. Client certificates require
`clientAuth`; server certificates require `serverAuth`.

Validate installed files:

```bash
openssl verify -CAfile infra/certs/ca.crt infra/certs/api_server.crt
openssl verify -CAfile infra/certs/ca.crt infra/certs/mqtt_server.crt
openssl verify -CAfile infra/certs/ca.crt infra/certs/backend_client.crt
openssl x509 -in infra/certs/mqtt_server.crt -noout -text
```

Bootstrap the first administrator after migrating:

```bash
make migrate-db
make bootstrap-admin
```
