package com.ayushbot.app

import android.app.Application
import com.ayushbot.app.core.di.AppContainer

/**
 * AyushBot Application class.
 * Initializes Room database and other app-level dependencies.
 */
class AyushBotApplication : Application() {
    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        appContainer = AppContainer(this)
        // Room database initialization and WorkManager sync can be wired here.
    }
}
