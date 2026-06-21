#include "lcd_display.h"

// =============================================================================
// I2C LCD Display Driver (16x2, PCF8574 backpack)
// Shares I2C bus with MAX30102 (SDA=21, SCL=22)
// =============================================================================

bool LCDDisplay::init() {
    Serial.println("[LCD] Initialising...");
    _lcd.init();
    _lcd.backlight();
    _lcd.clear();
    _lcd.setCursor(0, 0);
    _lcd.print("  AyushBot v1.0 ");
    _lcd.setCursor(0, 1);
    _lcd.print("  Initialising..");
    _initialised = true;
    Serial.println("[LCD] OK");
    return true;
}

// -----------------------------------------------------------------------------
// Line 1: "SpO2:98% HR:72 "
// Line 2: "T:36.8C W:3.2kg"
void LCDDisplay::showVitals(float spo2, float hr, float tempC, float weightKg) {
    if (!_initialised) return;

    char line1[17], line2[17];
    snprintf(line1, sizeof(line1), "SpO2:%2d%% HR:%3d ", (int)spo2, (int)hr);
    snprintf(line2, sizeof(line2), "T:%4.1fC W:%4.1fkg", tempC, weightKg);

    _lcd.setCursor(0, 0);
    _lcd.print(line1);
    _lcd.setCursor(0, 1);
    _lcd.print(line2);
}

// -----------------------------------------------------------------------------
void LCDDisplay::showStatus(const char* line1, const char* line2) {
    if (!_initialised) return;
    _lcd.clear();
    _lcd.setCursor(0, 0);
    _lcd.print(line1);
    _lcd.setCursor(0, 1);
    _lcd.print(line2);
}

// -----------------------------------------------------------------------------
// Full screen danger alert
void LCDDisplay::showDanger(float spo2, float hr) {
    if (!_initialised) return;
    char line2[17];
    snprintf(line2, sizeof(line2), "SpO2:%2d HR:%3d! ", (int)spo2, (int)hr);
    _lcd.setCursor(0, 0);
    _lcd.print("*** DANGER!!!***");
    _lcd.setCursor(0, 1);
    _lcd.print(line2);
}

// -----------------------------------------------------------------------------
void LCDDisplay::showBLEStatus(bool connected) {
    if (!_initialised) return;
    _lcd.setCursor(0, 0);
    _lcd.print(connected ? "BLE: Connected  " : "BLE: Waiting... ");
}

// -----------------------------------------------------------------------------
void LCDDisplay::clear() {
    if (_initialised) _lcd.clear();
}