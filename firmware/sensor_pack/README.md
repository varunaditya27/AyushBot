# AyushBot Sensor Pack Firmware

## Purpose

This directory contains the complete firmware for the AyushBot Arduino-based
physiological sensor pack — the hardware fail-safe layer (Layer 1) of the
AyushBot system.

The sensor pack is responsible for:

1. **Reading vital signs** from three sensors (SpO2/HR, Temperature, Weight)
2. **Fusing sensor data** via a Kalman filter for noise reduction
3. **Running a TinyML danger classifier** directly on the microcontroller
   (binary: DANGER / NOT DANGER) with sub-millisecond latency
4. **Transmitting readings** to the ASHA's Android phone over BLE GATT,
   encrypted with ASCON-128 lightweight cryptography
5. **Firing a hardware alarm** if critical danger signs are detected,
   independent of phone or gateway connectivity

## Target Hardware

- **Board:** Arduino Nano 33 BLE Sense (nRF52840, ARM Cortex-M4F @ 64 MHz)
- **RAM:** 256 KB
- **Flash:** 1 MB
- **Sensors:**
  - MAX30100 — Pulse oximetry (SpO2) + Heart Rate via PPG
  - DS18B20 — Digital temperature probe (1-Wire)
  - HX711 — Load cell amplifier for weight measurement

## Build System

Uses PlatformIO. See `platformio.ini` for board config, library deps, and
build flags.

## Directory Layout

```
src/
├── main.cpp           — Arduino entry point (setup + loop)
├── config.h           — Pin definitions, thresholds, constants
├── sensors/           — Individual sensor hardware drivers
├── fusion/            — Multi-sensor Kalman filter
├── tinyml/            — TFLite Micro model + inference engine
└── comms/             — BLE GATT service + ASCON-128 encryption
```

## Safety Design

The TinyML model is the system's **ultimate safety net**. It does not depend
on the Android phone, the PHC gateway, or any network connectivity. If the
phone crashes and the gateway is offline, this firmware still detects life-
threatening vital sign patterns and fires a local hardware alarm (buzzer/LED).
