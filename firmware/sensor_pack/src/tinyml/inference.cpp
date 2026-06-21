#include "inference.h"
#include "../config.h"

bool InferenceEngine::init() {
    Serial.println("[TinyML] Threshold fallback mode active");
    _initialised = true;
    return true;
}

DangerResult InferenceEngine::runInference(float inputs[MODEL_INPUT_FEATURES]) {
    return thresholdFallback(inputs[0], inputs[1], inputs[2]);
}

DangerResult InferenceEngine::thresholdFallback(float spo2, float hr, float temp) {
    DangerResult r = {false, 0.0f, 0};
    if (spo2 < SPO2_CRITICAL_LOW || hr > HR_CRITICAL_HIGH ||
        hr < HR_CRITICAL_LOW || temp > TEMP_HYPERPYREXIA ||
        temp < TEMP_HYPOTHERMIA) {
        r.isDanger = true;
        r.confidence = 1.0f;
    }
    Serial.printf("[TinyML] %s\n", r.isDanger ? "DANGER" : "SAFE");
    return r;
}
