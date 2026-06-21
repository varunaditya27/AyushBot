package com.ayushbot.app.sensor

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothGattService
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.pm.PackageManager
import android.os.ParcelUuid
import androidx.core.content.ContextCompat
import com.ayushbot.app.data.model.SensorReading
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID

data class SensorDevice(
    val name: String?,
    val address: String,
)

data class SensorConnectionState(
    val isScanning: Boolean = false,
    val isConnected: Boolean = false,
    val devices: List<SensorDevice> = emptyList(),
    val latestReading: SensorReading? = null,
    val error: String? = null,
)

class SensorBleClient(private val context: Context) {
    private val bluetoothManager = context.getSystemService(BluetoothManager::class.java)
    private val adapter: BluetoothAdapter? = bluetoothManager?.adapter
    private var gatt: BluetoothGatt? = null
    private val readings = mutableMapOf<UUID, Float>()
    private var dangerFlag = false

    private val _state = MutableStateFlow(SensorConnectionState())
    val state: StateFlow<SensorConnectionState> = _state

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device ?: return
            val sensor = SensorDevice(device.name, device.address)
            _state.value = _state.value.copy(
                devices = (_state.value.devices + sensor).distinctBy { it.address },
                error = null,
            )
        }

        override fun onScanFailed(errorCode: Int) {
            _state.value = _state.value.copy(
                isScanning = false,
                error = "BLE scan failed: $errorCode",
            )
        }
    }

    @SuppressLint("MissingPermission")
    fun startScan() {
        if (!hasBlePermissions()) {
            _state.value = _state.value.copy(error = "Bluetooth permissions are missing")
            return
        }
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null) {
            _state.value = _state.value.copy(error = "Bluetooth LE scanner unavailable")
            return
        }
        val filter = ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(BleUuids.service))
            .build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()
        scanner.startScan(listOf(filter), settings, scanCallback)
        _state.value = _state.value.copy(isScanning = true, error = null)
    }

    @SuppressLint("MissingPermission")
    fun stopScan() {
        if (hasBlePermissions()) {
            adapter?.bluetoothLeScanner?.stopScan(scanCallback)
        }
        _state.value = _state.value.copy(isScanning = false)
    }

    @SuppressLint("MissingPermission")
    fun connect(address: String) {
        if (!hasBlePermissions()) {
            _state.value = _state.value.copy(error = "Bluetooth permissions are missing")
            return
        }
        val device = adapter?.getRemoteDevice(address)
        if (device == null) {
            _state.value = _state.value.copy(error = "Sensor device not found")
            return
        }
        stopScan()
        gatt = device.connectGatt(context, false, callback, BluetoothDevice.TRANSPORT_LE)
    }

    @SuppressLint("MissingPermission")
    fun disconnect() {
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        _state.value = _state.value.copy(isConnected = false)
    }

    private val callback = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                _state.value = _state.value.copy(isConnected = true, error = null)
                gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                _state.value = _state.value.copy(isConnected = false)
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            val service = gatt.getService(BleUuids.service)
            if (service == null) {
                _state.value = _state.value.copy(error = "AyushBot sensor service not found")
                return
            }
            enableNotifications(gatt, service)
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
        ) {
            handleCharacteristic(characteristic.uuid, value)
        }

        @Deprecated("Deprecated by Android API, kept for older devices")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
        ) {
            handleCharacteristic(characteristic.uuid, characteristic.value ?: return)
        }
    }

    @SuppressLint("MissingPermission")
    private fun enableNotifications(gatt: BluetoothGatt, service: BluetoothGattService) {
        listOf(
            BleUuids.spo2,
            BleUuids.heartRate,
            BleUuids.temperature,
            BleUuids.weight,
            BleUuids.danger,
            BleUuids.signalQuality,
        ).forEach { uuid ->
            val characteristic = service.getCharacteristic(uuid) ?: return@forEach
            gatt.setCharacteristicNotification(characteristic, true)
            val descriptor = characteristic.getDescriptor(BleUuids.clientConfig)
            if (descriptor != null) {
                descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                gatt.writeDescriptor(descriptor)
            }
        }
    }

    private fun handleCharacteristic(uuid: UUID, value: ByteArray) {
        if (uuid == BleUuids.danger) {
            dangerFlag = decodeFloat(value) > 0f
        } else {
            readings[uuid] = decodeFloat(value)
        }
        val spo2 = readings[BleUuids.spo2]
        val hr = readings[BleUuids.heartRate]
        val temp = readings[BleUuids.temperature]
        if (spo2 != null && hr != null && temp != null) {
            _state.value = _state.value.copy(
                latestReading = SensorReading(
                    spo2 = spo2,
                    heartRate = hr,
                    temperature = temp,
                    signalQuality = readings[BleUuids.signalQuality] ?: 0f,
                    dangerFlag = dangerFlag,
                ),
                error = null,
            )
        }
    }

    private fun decodeFloat(value: ByteArray): Float {
        val text = value.toString(Charsets.UTF_8).trim()
        text.toFloatOrNull()?.let { return it }
        return when (value.size) {
            0 -> 0f
            1 -> value[0].toInt().toFloat()
            2 -> ByteBuffer.wrap(value).order(ByteOrder.LITTLE_ENDIAN).short.toFloat()
            else -> ByteBuffer.wrap(value.copyOfRange(0, minOf(4, value.size)).copyOf(4))
                .order(ByteOrder.LITTLE_ENDIAN)
                .float
        }
    }

    private fun hasBlePermissions(): Boolean {
        val scan = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.BLUETOOTH_SCAN,
        ) == PackageManager.PERMISSION_GRANTED
        val connect = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.BLUETOOTH_CONNECT,
        ) == PackageManager.PERMISSION_GRANTED
        return scan && connect
    }
}
