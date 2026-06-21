#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "MAX30105.h"       // SparkFun MAX3010x library covers MAX30102
#include "../config.h"

#define MOVING_AVG_WINDOW       4
#define SPO2_VARIANCE_THRESHOLD 4.0f

class MAX30102Sensor {
public:
    bool          init();
    void          update();
    float         getSpO2()          const;
    float         getHeartRate()     const;
    bool          isValid()          const;
    SignalQuality getSignalQuality() const;

private:
    MAX30105      _sensor;
    bool          _initialised   = false;
    bool          _isValid       = false;
    float         _spO2          = 0.0f;
    float         _heartRate     = 0.0f;
    SignalQuality _signalQuality = SIGNAL_NONE;

    // Raw buffers for SpO2 calculation
    uint32_t      _irBuffer[100]  = {0};
    uint32_t      _redBuffer[100] = {0};

    // Moving average
    float         _hrBuffer[MOVING_AVG_WINDOW]   = {0};
    float         _spo2Buffer[MOVING_AVG_WINDOW] = {0};
    uint8_t       _bufIdx = 0;

    SignalQuality _assessSignalQuality();
};