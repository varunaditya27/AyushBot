#include <Arduino.h>
#include "ble_gatt.h"
#include "../config.h"

static BLEGattServer* s_inst = nullptr;

class AgeWriteCb : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        uint16_t age = *(uint16_t*)c->getData();
        Serial.printf("[BLE] Patient age: %d months\n", age);
        if (s_inst && s_inst->onAgeWrittenCb) s_inst->onAgeWrittenCb(age);
    }
};

class ConnCb : public BLEServerCallbacks {
    void onConnect(BLEServer*) override {
        s_inst->_connected = true;
        Serial.println("[BLE] Connected");
    }
    void onDisconnect(BLEServer*) override {
        s_inst->_connected = false;
        Serial.println("[BLE] Disconnected — restarting advertising");
        BLEDevice::startAdvertising();
    }
};

bool BLEGattServer::init() {
    s_inst = this;
    BLEDevice::init(BLE_DEVICE_NAME);
    _server = BLEDevice::createServer();
    _server->setCallbacks(new ConnCb());

    BLEService* svc = _server->createService(BLEUUID(BLE_SERVICE_UUID), 30);

    auto mkChar = [&](const char* uuid, uint32_t props) -> BLECharacteristic* {
        auto* c = svc->createCharacteristic(uuid, props);
        if (props & BLECharacteristic::PROPERTY_NOTIFY) c->addDescriptor(new BLE2902());
        return c;
    };

    uint32_t RN = BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY;
    _charSpo2    = mkChar(BLE_CHAR_SPO2_UUID,           RN);
    _charHR      = mkChar(BLE_CHAR_HR_UUID,             RN);
    _charTemp    = mkChar(BLE_CHAR_TEMP_UUID,           RN);
    _charWeight  = mkChar(BLE_CHAR_WEIGHT_UUID,         RN);
    _charDanger  = mkChar(BLE_CHAR_DANGER_UUID,         RN);
    _charQuality = mkChar(BLE_CHAR_SIGNAL_QUALITY_UUID, RN);
    _charAge     = mkChar(BLE_CHAR_AGE_UUID, BLECharacteristic::PROPERTY_WRITE);
    _charAge->setCallbacks(new AgeWriteCb());

    svc->start();
    BLEAdvertising* adv = BLEDevice::getAdvertising();
    adv->addServiceUUID(BLE_SERVICE_UUID);
    adv->setScanResponse(true);
    BLEDevice::startAdvertising();
    Serial.println("[BLE] Advertising as: " BLE_DEVICE_NAME);
    return true;
}

void BLEGattServer::updateVitals(uint8_t spo2, uint16_t hr, float tempC,
    uint16_t weightGrams, const uint8_t* enc, size_t encLen)
{
    _charSpo2->setValue(&spo2, 1);
    _charHR->setValue((uint8_t*)&hr, 2);
    int16_t t = (int16_t)(tempC * 100);
    _charTemp->setValue((uint8_t*)&t, 2);
    _charWeight->setValue((uint8_t*)&weightGrams, 2);
    if (_connected) {
        _charSpo2->notify(); _charHR->notify();
        _charTemp->notify(); _charWeight->notify();
    }
}

void BLEGattServer::setDangerFlag(bool danger) {
    uint8_t f = danger ? 1 : 0;
    _charDanger->setValue(&f, 1);
    if (_connected) _charDanger->notify();
}

void BLEGattServer::setSignalQuality(SignalQuality q) {
    uint8_t v = (uint8_t)q;
    _charQuality->setValue(&v, 1);
    if (_connected) _charQuality->notify();
}

bool BLEGattServer::isConnected() const { return _connected; }