#pragma once
#include <Arduino.h>
#include "../config.h"

struct DangerResult {
    bool     isDanger;
    float    confidence;
    uint32_t inferenceTimeUs;
};

class InferenceEngine {
public:
    bool         init();
    DangerResult runInference(float inputs[MODEL_INPUT_FEATURES]);
    DangerResult thresholdFallback(float spo2, float hr, float temp);
private:
    bool _initialised = false;
};
