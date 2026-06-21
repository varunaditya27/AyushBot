package com.ayushbot.app.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.ayushbot.app.core.config.AppConfigLoader
import com.ayushbot.app.data.local.AyushBotDatabase
import com.ayushbot.app.data.remote.AuthTokenStore
import com.ayushbot.app.data.remote.BackendApiFactory
import com.ayushbot.app.data.repository.BackendCaseRepository
import java.util.concurrent.TimeUnit

class SyncCasesWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val config = AppConfigLoader(applicationContext).load()
        if (config.mock.useMockBackend) {
            return Result.success()
        }

        val database = AyushBotDatabase.getInstance(applicationContext)
        val tokenStore = AuthTokenStore(applicationContext)
        if (tokenStore.accessToken().isNullOrBlank()) {
            return Result.retry()
        }

        val api = BackendApiFactory.create(config.backend.baseUrl, tokenStore)
        val repository = BackendCaseRepository(
            api = api,
            patientDao = database.patientDao(),
            caseDao = database.caseDao(),
            recommendationDao = database.recommendationDao(),
        )
        val response = repository.syncPending().getOrElse {
            return Result.retry()
        }
        return if (response.rejected == 0) Result.success() else Result.retry()
    }

    companion object {
        private const val WORK_NAME = "sync-pending-cases"

        fun enqueue(context: Context) {
            val request = PeriodicWorkRequestBuilder<SyncCasesWorker>(
                repeatInterval = 15,
                repeatIntervalTimeUnit = TimeUnit.MINUTES,
            )
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    30,
                    TimeUnit.SECONDS,
                )
                .build()

            WorkManager.getInstance(context.applicationContext).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                request,
            )
        }
    }
}
