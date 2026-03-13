# =============================================================================
# AyushBot Tests — Integration: BLE → MQTT → Backend Data Flow
# =============================================================================
#
# PURPOSE:
#   Integration tests for the sensor data ingestion path:
#   Arduino (BLE) → Android Bridge (BLE→MQTT) → Mosquitto Broker → Backend API
#   Verifies that sensor data flows correctly from the MQTT broker to the
#   backend triage API.
#
# TEST CASES:
#
#   test_mqtt_message_received_by_backend
#     Setup: Start a test Mosquitto broker (Docker or in-memory mock)
#     Action: Publish a sensor payload to topic ayushbot/sensors/test_001/vitals
#     Expected: Backend's MQTT subscriber receives the payload and invokes
#       the triage pipeline
#
#   test_mqtt_payload_deserialization
#     Input: MQTT message with JSON payload:
#       {"device_id":"sensor_001","spo2":95,"hr":130,"temp":37.2,"ts":1234567890}
#     Expected: Payload correctly deserialized into the sensor data model.
#       All fields parsed with correct types.
#
#   test_mqtt_tls_authentication
#     Action: Attempt to connect to the broker WITHOUT a valid client certificate
#     Expected: Connection rejected (mTLS enforcement)
#
#   test_mqtt_acl_enforcement
#     Action: Authenticated client attempts to publish to a topic it does NOT
#       have write access to (e.g., android_bridge tries to publish to fl/gradients)
#     Expected: Publish rejected by the ACL rules
#
#   test_mqtt_message_ordering
#     Action: Publish 10 sensor readings with sequential timestamps
#     Expected: Backend receives them in order (QoS 1 guarantees)
#
#   test_ascon_encrypted_payload
#     Action: Publish an ASCON-128 encrypted sensor payload
#     Expected: Backend decrypts the payload before processing
#       (verifying the ASCON crypto integration)
#
# PREREQUISITES:
#   These tests require a running MQTT broker. In CI, use the Docker
#   Mosquitto container from docker-compose.yml. Locally, you can use
#   a minimal in-process MQTT broker mock.
#
# FIXTURES USED:
#   - sample_sensor_payload, test_config
# =============================================================================
