// =============================================================================
// AyushBot Sensor Pack — ASCON-128 Lightweight Encryption Module
// =============================================================================
//
// PURPOSE:
//   Implements ASCON-128 authenticated encryption with associated data (AEAD)
//   for securing vital sign payloads transmitted over BLE from the sensor pack
//   to the ASHA's Android phone. ASCON was selected as the NIST Lightweight
//   Cryptography Standard in 2023, making it the recommended cipher for
//   resource-constrained IoT devices.
//
// WHY ASCON INSTEAD OF AES/TLS:
//   - Standard TLS 1.2/1.3 is too compute-intensive for the Arduino's
//     Cortex-M4 processor (40-60 ms overhead per handshake vs <10 ms for ASCON)
//   - AES-128-GCM requires hardware AES support or large lookup tables;
//     ASCON achieves comparable security with a fraction of the code size
//     and CPU cycles.
//   - ASCON is specifically designed for constrained environments: its
//     permutation-based design uses only bitwise operations (AND, XOR, rotate),
//     no S-boxes or multiplication — perfect for microcontrollers.
//   - Published benchmarks on Raspberry Pi show ASCON achieving <10 ms RTT
//     overhead vs TLS's 40-60 ms for a 512-byte vital-sign payload.
//
// SECURITY PROPERTIES:
//   - ASCON-128 provides 128-bit security for both confidentiality and
//     authenticity (AEAD mode).
//   - The 128-bit authentication tag ensures the phone can verify that the
//     payload has not been tampered with in transit.
//   - Associated Data (AD) field carries the unencrypted packet header
//     (sensor pack ID, sequence number) for replay attack prevention.
//
// KEY MANAGEMENT:
//   For the prototype:
//     - A pre-shared 128-bit key is hardcoded (in config.h or stored in flash)
//     - The same key is provisioned into the Android app at pairing time
//   For production:
//     - Key exchange via BLE Secure Connection (ECDH) at initial pairing
//     - Keys rotated periodically or per session
//     - Option to use the nRF52840's ARM CryptoCell hardware secure element
//
// NONCE MANAGEMENT:
//   - ASCON-128 requires a 128-bit nonce that must never be reused with the
//     same key. The nonce is constructed from:
//       [device_id (32 bits) | boot_counter (32 bits) | packet_counter (64 bits)]
//   - The packet counter is monotonically incrementing and persisted in flash
//     across reboots to guarantee uniqueness.
//
// INTERFACE:
//   - init(key): Initialize ASCON context with the 128-bit pre-shared key
//   - encrypt(plaintext, plaintext_len, ad, ad_len, nonce) -> ciphertext + tag
//   - decrypt(ciphertext, ct_len, ad, ad_len, nonce, tag) -> plaintext or FAIL
//   - generateNonce() -> fresh 128-bit nonce using device_id + counters
//
// IMPLEMENTATION NOTE:
//   Uses the reference ASCON-128 C implementation from the NIST submission
//   (https://github.com/ascon/ascon-c), adapted for Arduino's toolchain.
//   The entire ASCON library compiles to approximately 2 KB of Flash.
// =============================================================================
