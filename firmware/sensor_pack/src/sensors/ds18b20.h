#pragma once
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

class DS18B20Sensor {
public:
    bool  init();
    void  update();
    float getTemperature() const;
    bool  isValid()        const;

private:
    OneWire*           _oneWire       = nullptr;
    DallasTemperature* _dallas        = nullptr;
    bool               _initialised   = false;
    bool               _isValid       = false;
    float              _temperatureC  = 0.0f;
    uint32_t           _lastRequestMs = 0;
};