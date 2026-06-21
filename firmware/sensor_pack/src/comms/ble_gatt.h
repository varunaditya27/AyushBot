#pragma once
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <functional>
#include "../config.h"

class BLEGattServer {
public:
    bool init();
    void updateVitals(uint8_t spo2, uint16_t hr, float tempC, uint16_t weightGrams, const uint8_t* encPayload, size_t payloadLen);
    void setDangerFlag(bool danger);
    void setSignalQuality(SignalQuality quality);
    bool isConnected() const;
    std::function<void(uint16_t ageMos)> onAgeWrittenCb;
    bool _connected = false;
private:
    BLEServer* _server = nullptr;
    BLECharacteristic* _charSpo2 = nullptr;
    BLECharacteristic* _charHR = nullptr;
    BLECharacteristic* _charTemp = nullptr;
    BLECharacteristic* _charWeight = nullptr;
    BLECharacteristic* _charDanger = nullptr;
    BLECharacteristic* _charAge = nullptr;
    BLECharacteristic* _charQuality = nullptr;
};
