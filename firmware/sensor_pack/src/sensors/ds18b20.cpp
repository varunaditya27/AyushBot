#include "ds18b20.h"
#include "../config.h"

bool DS18B20Sensor::init() {
    Serial.println("[DS18B20] Initialising...");
    _oneWire = new OneWire(DS18B20_ONE_WIRE_PIN);
    _dallas  = new DallasTemperature(_oneWire);
    _dallas->begin();

    if (_dallas->getDeviceCount() == 0) {
        Serial.println("[DS18B20] FAILED — check probe + 4.7kΩ pull-up resistor");
        return false;
    }
    Serial.printf("[DS18B20] Found %d device(s)\n", _dallas->getDeviceCount());
    _dallas->setResolution(12);
    _dallas->setWaitForConversion(false);
    _dallas->requestTemperatures();
    _lastRequestMs = millis();
    _initialised = true;
    Serial.println("[DS18B20] OK");
    return true;
}

void DS18B20Sensor::update() {
    if (!_initialised) return;
    if (millis() - _lastRequestMs < 800) return;

    float raw = _dallas->getTempCByIndex(0);
    if (raw > -100.0f && raw < 60.0f) {
        _temperatureC = raw + TEMP_AXILLARY_OFFSET;
        _isValid = true;
    } else {
        Serial.println("[DS18B20] Read error — check probe contact");
        _isValid = false;
    }
    _dallas->requestTemperatures();
    _lastRequestMs = millis();
}

float DS18B20Sensor::getTemperature() const { return _temperatureC; }
bool  DS18B20Sensor::isValid()         const { return _isValid; }