# ESP32 Telemetry Contract

The intended AyushBot visit flow is ESP32 sensor pack -> Android over BLE -> Room -> backend HTTP sync. The ESP32 should not run the Python backend and should not be required to reach the backend for offline diagnosis.

This file documents an optional direct-MQTT lab path for diagnostics or experiments. Do not use it as the primary Android integration contract.

## Transport

Preferred local-showcase transport:

```text
MQTT topic: ayushbot/telemetry/<device_id>
Payload: UTF-8 JSON
```

The backend subscribes to `ayushbot/telemetry/#` by default when `mqtt.enabled: true`. If `device_id` is omitted from the JSON body, the backend uses the final topic segment as the device id.

## Payload

```json
{
  "id": "esp32-demo-01-000001",
  "device_id": "esp32-demo-01",
  "event_type": "vitals",
  "timestamp": 1710000000000,
  "case_id": null,
  "readings": {
    "spo2": 97,
    "heart_rate": 104,
    "respiratory_rate": 32,
    "temperature_c": 37.2,
    "signal_quality": {
      "spo2": 0.95
    }
  }
}
```

Required fields:

- `id`: unique telemetry event id. Use a UUID or a device id plus monotonically increasing sequence number.
- `timestamp`: Unix epoch milliseconds from the ESP32 or gateway clock.
- `readings`: object containing the vitals actually measured. Do not send missing values as zero.

Optional fields:

- `device_id`: required only when the topic does not end with the device id.
- `event_type`: defaults to `mqtt`.
- `case_id`: include only when telemetry is already associated with a backend case.

## Development Behavior

For college showcase/local development, the first valid MQTT message from an unknown ESP32 auto-registers a backend `SENSOR` device with status `ACTIVE`. Reusing the same event `id` is idempotent and will not create a duplicate telemetry row.

If a device already exists with status `INACTIVE` or `REVOKED`, MQTT telemetry from that device is discarded.

## Local Config

Enable MQTT in `backend/config.yaml` when using a broker:

```yaml
mqtt:
  enabled: true
  host: 127.0.0.1
  port: 1883
  topic: ayushbot/telemetry/#
  tls_enabled: false
```

Use the backend host IP address in ESP32 firmware, for example `192.168.1.20`, not `localhost`.

Production-style deployments should enable MQTT TLS/mTLS and use a device certificate common name that matches the ESP32 `device_id`.
