#include "kalman.h"

void KalmanFilter::init() {
    _x[SPO2] = 98.0f; _x[HR] = 80.0f; _x[TEMP] = 36.5f;
    _p[SPO2] = 10.0f; _p[HR] = 25.0f; _p[TEMP] = 2.0f;
    _q[SPO2] = 0.1f;  _q[HR] = 1.0f;  _q[TEMP] = 0.01f;
    _r[SPO2] = 4.0f;  _r[HR] = 9.0f;  _r[TEMP] = 0.25f;
    Serial.println("[Kalman] Initialised");
}

void KalmanFilter::predict() {
    for (int i = 0; i < NUM_STATES; i++) _p[i] += _q[i];
}

void KalmanFilter::update(SensorChannel channel, float measurement) {
    int i = (int)channel;
    float innovation = measurement - _x[i];
    float mahal = (innovation * innovation) / (_p[i] + _r[i]);
    if (mahal > 9.0f) {
        Serial.printf("[Kalman] Outlier rejected ch=%d\n", i);
        return;
    }
    float k = _p[i] / (_p[i] + _r[i]);
    _x[i] = _x[i] + k * innovation;
    _p[i] = (1.0f - k) * _p[i];
}

void KalmanFilter::getState(float& spo2, float& hr, float& temp) const {
    spo2 = _x[SPO2]; hr = _x[HR]; temp = _x[TEMP];
}

void KalmanFilter::getUncertainty(float& pSpo2, float& pHr, float& pTemp) const {
    pSpo2 = _p[SPO2]; pHr = _p[HR]; pTemp = _p[TEMP];
}