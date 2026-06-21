package com.ayushbot.app.sensor

import java.util.UUID

object BleUuids {
    val service: UUID = UUID.fromString("a7a5ab07-0001-1000-8000-00805f9b34fb")
    val spo2: UUID = UUID.fromString("a7a5ab07-0002-1000-8000-00805f9b34fb")
    val heartRate: UUID = UUID.fromString("a7a5ab07-0003-1000-8000-00805f9b34fb")
    val temperature: UUID = UUID.fromString("a7a5ab07-0004-1000-8000-00805f9b34fb")
    val weight: UUID = UUID.fromString("a7a5ab07-0005-1000-8000-00805f9b34fb")
    val danger: UUID = UUID.fromString("a7a5ab07-0006-1000-8000-00805f9b34fb")
    val age: UUID = UUID.fromString("a7a5ab07-0007-1000-8000-00805f9b34fb")
    val signalQuality: UUID = UUID.fromString("a7a5ab07-0008-1000-8000-00805f9b34fb")
    val clientConfig: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
}
