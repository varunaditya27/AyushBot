#pragma once
#include <Arduino.h>

enum SensorChannel { SPO2 = 0, HR = 1, TEMP = 2, NUM_STATES = 3 };

class KalmanFilter {
public:
    void init();
    void predict();
    void update(SensorChannel channel, float measurement);
    void getState(float& spo2, float& hr, float& temp) const;
    void getUncertainty(float& pSpo2, float& pHr, float& pTemp) const;

private:
    float _x[NUM_STATES];
    float _p[NUM_STATES];
    float _q[NUM_STATES];
    float _r[NUM_STATES];
};