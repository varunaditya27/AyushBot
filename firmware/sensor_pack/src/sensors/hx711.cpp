#include "hx711.h"
#include "../config.h"

bool HX711Sensor::init() {
    Serial.println("[HX711] Initialising...");
    _scale.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
    if (!_scale.is_ready()) {
        Serial.println("[HX711] FAILED — chip not responding");
        return false;
    }
    _scale.set_scale(HX711_CALIBRATION_FACTOR);
    _scale.tare(HX711_AVERAGING_SAMPLES);
    _initialised = true;
    Serial.println("[HX711] OK — 5kg load cell tared");
    return true;
}

void HX711Sensor::tare() {
    if (!_initialised) return;
    Serial.println("[HX711] Taring...");
    _scale.tare(HX711_AVERAGING_SAMPLES);
    Serial.println("[HX711] Tare done");
}

void HX711Sensor::update() {
    if (!_initialised || !_scale.is_ready()) return;

    float raw = _scale.get_units(HX711_AVERAGING_SAMPLES);
    if (raw < 0.0f) raw = 0.0f;
    if (raw > WEIGHT_MAX_KG) {
        Serial.printf("[HX711] Spike rejected: %.2f kg\n", raw);
        return;
    }

    _isStable = (abs(raw - _weightKg) < STABLE_TOLERANCE_KG);
    _weightKg = raw;
    _isValid  = (_weightKg >= WEIGHT_MIN_KG);
}

float HX711Sensor::getWeight() const { return _weightKg; }
bool  HX711Sensor::isValid()   const { return _isValid; }
bool  HX711Sensor::isStable()  const { return _isStable; }