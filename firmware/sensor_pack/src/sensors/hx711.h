#pragma once
#include <Arduino.h>
#include <HX711.h>

#define STABLE_TOLERANCE_KG 0.05f

class HX711Sensor {
public:
    bool  init();
    void  update();
    void  tare();
    float getWeight() const;
    bool  isValid()   const;
    bool  isStable()  const;

private:
    HX711  _scale;
    bool   _initialised = false;
    bool   _isValid     = false;
    bool   _isStable    = false;
    float  _weightKg    = 0.0f;
};