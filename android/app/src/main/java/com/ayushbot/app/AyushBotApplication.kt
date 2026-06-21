package com.ayushbot.app

import android.app.Application
import com.ayushbot.app.core.di.AppContainer
import com.ayushbot.app.sync.SyncCasesWorker

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
        SyncCasesWorker.enqueue(this)
    }
}
