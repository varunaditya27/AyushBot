package com.ayushbot.app.voice.audio

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.util.concurrent.atomic.AtomicBoolean

class AudioRecorder(private val sampleRate: Int) {
    private val isRecording = AtomicBoolean(false)
    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    private val recordedSamples = mutableListOf<Short>()

    fun start(): Boolean {
        if (isRecording.get()) return true
        val bufferSize = AudioRecord.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        if (bufferSize == AudioRecord.ERROR || bufferSize == AudioRecord.ERROR_BAD_VALUE) {
            return false
        }

        val recorder = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize,
        )

        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            return false
        }

        recordedSamples.clear()
        isRecording.set(true)
        audioRecord = recorder
        recorder.startRecording()

        recordingThread = Thread {
            val buffer = ShortArray(bufferSize)
            while (isRecording.get()) {
                val read = recorder.read(buffer, 0, buffer.size)
                if (read > 0) {
                    synchronized(recordedSamples) {
                        for (i in 0 until read) {
                            recordedSamples.add(buffer[i])
                        }
                    }
                }
            }
        }.also { it.start() }

        return true
    }

    fun stop(): ShortArray {
        if (!isRecording.get()) return ShortArray(0)
        isRecording.set(false)
        recordingThread?.join(500)
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        val samples = synchronized(recordedSamples) { recordedSamples.toShortArray() }
        recordedSamples.clear()
        return samples
    }

    fun cancel() {
        if (!isRecording.get()) return
        isRecording.set(false)
        recordingThread?.join(500)
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        recordedSamples.clear()
    }

    fun isActive(): Boolean = isRecording.get()
}
