// =============================================================================
// AyushBot Sensor Pack — BLE GATT Service & Characteristics
// =============================================================================
//
// PURPOSE:
//   Implements the Bluetooth Low Energy (BLE) Generic Attribute Profile (GATT)
//   server that exposes the sensor pack's vital sign data to the ASHA's
//   Android phone. This is the primary communication channel between the
//   hardware sensor layer (Layer 1) and the mobile app layer (Layer 2).
//
// BLE SERVICE DESIGN:
//   One custom GATT service ("AyushBot Vital Signs Service") with the
//   following characteristics:
//
//   1. SpO2 Characteristic (READ + NOTIFY)
//      - 8-bit unsigned integer (0-100%)
//      - Notifies the phone whenever a new reading is available
//
//   2. Heart Rate Characteristic (READ + NOTIFY)
//      - 16-bit unsigned integer (BPM)
//      - Notifies on each new reading
//
//   3. Temperature Characteristic (READ + NOTIFY)
//      - 16-bit signed integer (Celsius × 100 for 2 decimal places)
//      - Notifies on each new reading
//
//   4. Weight Characteristic (READ + NOTIFY)
//      - 16-bit unsigned integer (grams)
//      - Notifies once when weight measurement stabilises
//
//   5. Danger Flag Characteristic (READ + NOTIFY)
//      - 8-bit boolean (0 = safe, 1 = danger detected by TinyML)
//      - Notifies immediately when danger state changes
//      - This is the highest-priority characteristic — the phone should
//        display an emergency alert immediately upon receiving a 1.
//
//   6. Patient Age Characteristic (WRITE)
//      - 16-bit unsigned integer (age in months)
//      - Written by the Android phone at the start of each encounter
//      - Used as an input feature for the TinyML classifier
//
//   7. Signal Quality Characteristic (READ + NOTIFY)
//      - 8-bit enum: 0 = GOOD, 1 = POOR (motion artifact), 2 = NO_SIGNAL
//      - Allows the phone to prompt the ASHA to re-attach the sensor
//
// DATA ENCRYPTION:
//   All characteristic values are encrypted with ASCON-128 before being
//   written to the GATT database. The phone (BLE central) must decrypt
//   using the shared ASCON key. This provides application-layer encryption
//   on top of BLE's native link-layer encryption.
//
// ADVERTISING:
//   - Device name: "AyushBot-<DEVICE_ID>" (unique per sensor pack)
//   - Advertising interval: balanced between discoverability and battery
//     (e.g., 100-200 ms when not connected, wider when idle)
//   - Includes the custom service UUID in the advertising packet so the
//     Android app can filter and auto-connect.
//
// CONNECTION LIFECYCLE:
//   - On connect: Pause advertising, enable notifications on all characteristics
//   - On disconnect: Resume advertising, continue local monitoring + alarming
//     (the TinyML classifier runs regardless of BLE connection state)
//   - Maximum one connected central at a time (the ASHA's phone)
//
// INTERFACE:
//   - init(): Configure GATT service, register characteristics, start advertising
//   - updateVitals(spo2, hr, temp, weight): Update characteristic values + notify
//   - setDangerFlag(bool danger): Update danger characteristic + notify
//   - setSignalQuality(quality): Update signal quality characteristic
//   - isConnected(): Check if a BLE central is currently connected
//   - onAgeWritten(callback): Register callback for when phone writes patient age
// =============================================================================
