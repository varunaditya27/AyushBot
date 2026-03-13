<div align="center">

# 📟 Sensor Pack Main Firmware

**ESP32 BLE Peripheral Configuration**

</div>

## 📌 Overview

The `/firmware/sensor_pack` directory contains the primary PlatformIO project for the physical AyushBot wearable. It bridges the raw I2C hardware sensors, runs them through the DSP/TinyML filters, and advertises the resulting clinical vitals as a standard Bluetooth Low Energy (BLE) GATT server.

## ⚙️ Software Architecture

The firmware utilizes **FreeRTOS** to handle multitasking across the dual-core ESP32, ensuring that heavy I2C polling does not block the BLE transmission stack.

```mermaid
graph TD
    subgraph FreeRTOS Tasks
        Task1[Task 1: Sensor Polling<br/>(Core 0)]:::task
        Task2[Task 2: TinyML Inference<br/>(Core 1)]:::task
        Task3[Task 3: BLE Server<br/>(Core 0)]:::task
    end
    
    Queue[(FreeRTOS Queue<br/>Raw PPG Buffers)]:::queue
    Mutex((I2C Mutex)):::mutex
    
    Task1 -- Write --> Queue
    Task1 -- Lock/Unlock --> Mutex
    
    Queue -- Read --> Task2
    Task2 -- Clean State --> Task3
    
    classDef task fill:#e3f2fd,stroke:#1565c0
    classDef queue fill:#fff3e0,stroke:#e65100
    classDef mutex fill:#f3e5f5,stroke:#7b1fa2
```

## 🧩 Modularity Structure

- **`src/main.cpp`**: Bootstraps the RTOS tasks and defines the GATT Service UUIDs (Heart Rate Service, Pulse Oximeter Service, Health Thermometer Service).
- **`lib/`**: Contains optimized wrappers for the MAX30102 and MLX90614 sensors.
- **`platformio.ini`**: Defines the hardware target (`esp32dev`), baud rates, and library dependencies.

## 🛠️ Status LEDs
The firmware operates a simple RGB LED on the chassis:
- 🔵 **Blinking Blue**: Advertising / Waiting for Android tablet to pair.
- 🟢 **Solid Green**: Paired and actively transmitting clean signals.
- 🔴 **Blinking Red**: Motion artifact detected or sensor physically removed from finger.

## 🚀 Flashing
```bash
cd firmware/sensor_pack
pio run -t upload
```
