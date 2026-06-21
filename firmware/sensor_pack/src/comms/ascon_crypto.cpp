#include "ascon_crypto.h"
#include "../config.h"

#define ASCON_128_RATE      8
#define ASCON_128_PA_ROUNDS 12
#define ASCON_128_PB_ROUNDS 6

struct AsconState { uint64_t x[5]; };

static inline uint64_t rotr64(uint64_t x, int n) {
    return (x >> n) | (x << (64 - n));
}

static void asconPermutation(AsconState& s, int rounds) {
    static const uint64_t RC[12] = {
        0xf0,0xe1,0xd2,0xc3,0xb4,0xa5,0x96,0x87,0x78,0x69,0x5a,0x4b
    };
    for (int r = 12 - rounds; r < 12; r++) {
        s.x[2] ^= RC[r];
        s.x[0] ^= s.x[4]; s.x[4] ^= s.x[3]; s.x[2] ^= s.x[1];
        uint64_t t[5];
        for (int i=0;i<5;i++) t[i]=~s.x[i];
        s.x[0]^=t[1]&s.x[1]; s.x[1]^=t[2]&s.x[2];
        s.x[2]^=t[3]&s.x[3]; s.x[3]^=t[4]&s.x[4]; s.x[4]^=t[0]&s.x[0];
        s.x[1]^=s.x[0]; s.x[0]^=s.x[4]; s.x[3]^=s.x[2]; s.x[2]=~s.x[2];
        s.x[0]^=rotr64(s.x[0],19)^rotr64(s.x[0],28);
        s.x[1]^=rotr64(s.x[1],61)^rotr64(s.x[1],39);
        s.x[2]^=rotr64(s.x[2], 1)^rotr64(s.x[2], 6);
        s.x[3]^=rotr64(s.x[3],10)^rotr64(s.x[3],17);
        s.x[4]^=rotr64(s.x[4], 7)^rotr64(s.x[4],41);
    }
}

bool AsconCrypto::init(const uint8_t key[ASCON_KEY_LEN]) {
    memcpy(_key, key, ASCON_KEY_LEN);
    _packetCounter = 0; _bootCounter++;
    Serial.println("[ASCON] Encryption context initialised");
    return true;
}

void AsconCrypto::generateNonce(uint8_t nonce[ASCON_NONCE_LEN]) {
    uint32_t devId = DEVICE_ID;
    memcpy(nonce,     &devId,          4);
    memcpy(nonce+4,   &_bootCounter,   4);
    memcpy(nonce+8,   &_packetCounter, 8);
    _packetCounter++;
}

size_t AsconCrypto::encrypt(
    const uint8_t* pt, size_t pt_len,
    const uint8_t* ad, size_t ad_len,
    const uint8_t  nonce[ASCON_NONCE_LEN],
    uint8_t* out)
{
    AsconState s;
    s.x[0] = 0x80400c0600000000ULL;
    memcpy(&s.x[1],_key,8); memcpy(&s.x[2],_key+8,8);
    memcpy(&s.x[3],nonce,8); memcpy(&s.x[4],nonce+8,8);
    asconPermutation(s, ASCON_128_PA_ROUNDS);
    s.x[3]^=((uint64_t*)_key)[0]; s.x[4]^=((uint64_t*)_key)[1];

    if (ad_len > 0) {
        size_t off=0;
        while (off < ad_len) {
            uint64_t blk=0; size_t chunk=min((size_t)8,ad_len-off);
            memcpy(&blk,ad+off,chunk);
            if(chunk<8) blk^=(0x80ULL<<(56-chunk*8));
            s.x[0]^=blk; asconPermutation(s,ASCON_128_PB_ROUNDS); off+=chunk;
        }
    }
    s.x[4]^=1ULL;

    size_t off=0;
    while (off < pt_len) {
        uint64_t blk=0; size_t chunk=min((size_t)8,pt_len-off);
        memcpy(&blk,pt+off,chunk);
        if(chunk<8) blk^=(0x80ULL<<(56-chunk*8));
        s.x[0]^=blk; memcpy(out+off,&s.x[0],chunk);
        if(chunk==8) asconPermutation(s,ASCON_128_PB_ROUNDS);
        off+=chunk;
    }

    s.x[1]^=((uint64_t*)_key)[0]; s.x[2]^=((uint64_t*)_key)[1];
    asconPermutation(s,ASCON_128_PA_ROUNDS);
    s.x[3]^=((uint64_t*)_key)[0]; s.x[4]^=((uint64_t*)_key)[1];
    memcpy(out+pt_len,&s.x[3],8); memcpy(out+pt_len+8,&s.x[4],8);
    return pt_len + ASCON_TAG_LEN;
}