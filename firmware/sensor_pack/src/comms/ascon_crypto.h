#pragma once
#include <Arduino.h>
#include "../config.h"

class AsconCrypto {
public:
    bool   init(const uint8_t key[ASCON_KEY_LEN]);
    void   generateNonce(uint8_t nonce[ASCON_NONCE_LEN]);
    size_t encrypt(const uint8_t* plaintext, size_t pt_len,
                   const uint8_t* ad, size_t ad_len,
                   const uint8_t  nonce[ASCON_NONCE_LEN],
                   uint8_t* output);
private:
    uint8_t  _key[ASCON_KEY_LEN] = {0};
    uint32_t _bootCounter        = 0;
    uint64_t _packetCounter      = 0;
};