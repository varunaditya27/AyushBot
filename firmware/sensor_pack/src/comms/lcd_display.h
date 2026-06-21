#pragma once
#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include "../config.h"

class LCDDisplay {
public:
    bool init();

    // Show vitals on LCD
    // Line 1: SpO2 + HR
    // Line 2: Temp + Weight
    void showVitals(float spo2, float hr, float tempC, float weightKg);

    // Show status message (e.g. "Waiting..." "No finger")
    void showStatus(const char* line1, const char* line2 = "");

    // Show DANGER alert — full screen
    void showDanger(float spo2, float hr);

    // Show BLE connection state
    void showBLEStatus(bool connected);

    void clear();

private:
    LiquidCrystal_I2C _lcd = LiquidCrystal_I2C(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);
    bool _initialised = false;
};