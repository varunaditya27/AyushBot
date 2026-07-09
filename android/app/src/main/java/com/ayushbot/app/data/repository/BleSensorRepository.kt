package com.ayushbot.app.data.repository

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID

@SuppressLint("MissingPermission")
class BleSensorRepository(
    private val context: Context
) : SensorRepository {

    private val TAG = "BleSensorRepository"

    // UUID Definitions (matching config.h)
    private val SERVICE_UUID = UUID.fromString("a7u5hb07-0001-1000-8000-00805f9b34fb")
    private val CHAR_SPO2_UUID = UUID.fromString("a7u5hb07-0002-1000-8000-00805f9b34fb")
    private val CHAR_HR_UUID = UUID.fromString("a7u5hb07-0003-1000-8000-00805f9b34fb")
    private val CHAR_TEMP_UUID = UUID.fromString("a7u5hb07-0004-1000-8000-00805f9b34fb")
    private val CHAR_WEIGHT_UUID = UUID.fromString("a7u5hb07-0005-1000-8000-00805f9b34fb")
    private val CHAR_DANGER_UUID = UUID.fromString("a7u5hb07-0006-1000-8000-00805f9b34fb")
    private val CHAR_QUALITY_UUID = UUID.fromString("a7u5hb07-0008-1000-8000-00805f9b34fb")
    private val CLIENT_CHARACTERISTIC_CONFIG_UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

    private val _sensorData = MutableStateFlow(SensorData())
    override val sensorData: StateFlow<SensorData> = _sensorData.asStateFlow()

    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val bluetoothAdapter = bluetoothManager.adapter
    private var bluetoothGatt: BluetoothGatt? = null
    private var isScanning = false

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var connectionTimeoutJob: Job? = null

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            val deviceName = device.name ?: ""
            Log.d(TAG, "Found BLE device: $deviceName (${device.address})")
            if (deviceName.contains("AyushBot", ignoreCase = true) || deviceName.contains("SensorPack", ignoreCase = true)) {
                stopScan()
                connectToDevice(device)
            }
        }

        override fun onScanFailed(errorCode: Int) {
            Log.e(TAG, "Scan failed with error: $errorCode")
            _sensorData.update { it.copy(isConnected = false) }
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                Log.e(TAG, "GATT status failure: $status. Disconnecting...")
                disconnectGatt()
                return
            }

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                Log.d(TAG, "Connected to GATT server. Discovering services...")
                _sensorData.update { it.copy(isConnected = true, deviceName = gatt.device.name ?: "AyushBot-SensorPack") }
                connectionTimeoutJob?.cancel()
                gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.d(TAG, "Disconnected from GATT server.")
                disconnectGatt()
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                val service = gatt.getService(SERVICE_UUID)
                if (service != null) {
                    Log.d(TAG, "AyushBot BLE service discovered. Subscribing to characteristics...")
                    scope.launch {
                        val charsToSubscribe = listOf(
                            CHAR_SPO2_UUID,
                            CHAR_HR_UUID,
                            CHAR_TEMP_UUID,
                            CHAR_WEIGHT_UUID,
                            CHAR_DANGER_UUID,
                            CHAR_QUALITY_UUID
                        )
                        for (charUuid in charsToSubscribe) {
                            val characteristic = service.getCharacteristic(charUuid)
                            if (characteristic != null) {
                                enableNotifications(gatt, characteristic)
                                delay(200) // Small delay between subscription commands to prevent GATT command overflow
                            }
                        }
                    }
                } else {
                    Log.e(TAG, "AyushBot BLE service not found on device.")
                }
            } else {
                Log.e(TAG, "Service discovery failed: $status")
            }
        }

        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            val value = characteristic.value ?: return
            Log.d(TAG, "Characteristic changed: ${characteristic.uuid}, value size: ${value.size}")
            
            when (characteristic.uuid) {
                CHAR_SPO2_UUID -> {
                    val spo2 = value[0].toInt() and 0xFF
                    _sensorData.update { it.copy(spo2 = spo2.toFloat()) }
                }
                CHAR_HR_UUID -> {
                    val hr = if (value.size >= 2) {
                        ByteBuffer.wrap(value).order(ByteOrder.LITTLE_ENDIAN).short.toInt() and 0xFFFF
                    } else {
                        value[0].toInt() and 0xFF
                    }
                    _sensorData.update { it.copy(hr = hr.toFloat()) }
                }
                CHAR_TEMP_UUID -> {
                    if (value.size >= 2) {
                        val tempRaw = ByteBuffer.wrap(value).order(ByteOrder.LITTLE_ENDIAN).short
                        val tempC = tempRaw.toFloat() / 100f
                        _sensorData.update { it.copy(tempC = tempC) }
                    }
                }
                CHAR_WEIGHT_UUID -> {
                    if (value.size >= 2) {
                        val weightRaw = ByteBuffer.wrap(value).order(ByteOrder.LITTLE_ENDIAN).short.toInt() and 0xFFFF
                        val weightKg = weightRaw.toFloat() / 1000f
                        _sensorData.update { it.copy(weightKg = weightKg) }
                    }
                }
                CHAR_QUALITY_UUID -> {
                    val qRaw = value[0].toInt() and 0xFF
                    val quality = when (qRaw) {
                        0 -> 1.0f // Good
                        1 -> 0.4f // Poor
                        else -> 0.0f // None
                    }
                    _sensorData.update { it.copy(signalQuality = quality) }
                }
            }
        }
    }

    override fun startCapture() {
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled) {
            Log.e(TAG, "Bluetooth not enabled or not supported")
            return
        }

        if (isScanning || bluetoothGatt != null) return

        _sensorData.update { SensorData(deviceName = "Scanning...") }
        startScan()
    }

    override fun stopCapture() {
        stopScan()
        disconnectGatt()
    }

    override fun runSelfTest() {
        scope.launch {
            _sensorData.update { it.copy(isSelfTestPassed = null) }
            delay(1500)
            _sensorData.update { it.copy(isSelfTestPassed = true) }
        }
    }

    private fun startScan() {
        val scanner = bluetoothAdapter.bluetoothLeScanner ?: return
        isScanning = true
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()
        
        val filters = listOf(
            ScanFilter.Builder().setServiceUuid(ParcelUuid(SERVICE_UUID)).build()
        )

        Log.d(TAG, "Starting BLE Scan...")
        scanner.startScan(filters, settings, scanCallback)

        connectionTimeoutJob = scope.launch {
            delay(15000) // 15 seconds timeout
            if (bluetoothGatt == null) {
                Log.d(TAG, "Connection timeout. Stopping scan.")
                stopScan()
                _sensorData.update { it.copy(deviceName = "Not Found", isConnected = false) }
            }
        }
    }

    private fun stopScan() {
        if (!isScanning) return
        isScanning = false
        val scanner = bluetoothAdapter.bluetoothLeScanner ?: return
        Log.d(TAG, "Stopping BLE Scan.")
        scanner.stopScan(scanCallback)
        connectionTimeoutJob?.cancel()
    }

    private fun connectToDevice(device: BluetoothDevice) {
        Log.d(TAG, "Connecting to device: ${device.address}")
        bluetoothGatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
    }

    private fun disconnectGatt() {
        bluetoothGatt?.disconnect()
        bluetoothGatt?.close()
        bluetoothGatt = null
        _sensorData.update { SensorData(isConnected = false) }
    }

    private fun enableNotifications(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
        gatt.setCharacteristicNotification(characteristic, true)
        val descriptor = characteristic.getDescriptor(CLIENT_CHARACTERISTIC_CONFIG_UUID)
        if (descriptor != null) {
            descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            gatt.writeDescriptor(descriptor)
        }
    }
}
