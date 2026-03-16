package com.ayushbot.app

import android.app.Application

/**
 * AyushBot Application class.
 * Initializes Room database and other app-level dependencies.
 */
class AyushBotApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Room database initialization will be added here
        // WorkManager initialization for background sync
    }
}
