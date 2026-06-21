package com.ayushbot.app.data.repository

import com.ayushbot.app.data.remote.AuthTokenStore
import com.ayushbot.app.data.remote.BackendApi
import com.ayushbot.app.data.remote.model.CurrentUserResponse
import com.ayushbot.app.data.remote.model.LoginRequest
import com.ayushbot.app.data.remote.model.RefreshRequest

class AuthRepository(
    private val api: BackendApi,
    private val tokenStore: AuthTokenStore,
) {
    suspend fun login(username: String, password: String, deviceId: String): Result<Unit> {
        return runCatching {
            val tokens = api.login(
                LoginRequest(
                    username = username,
                    password = password,
                    deviceId = deviceId,
                )
            )
            tokenStore.save(tokens)
        }
    }

    suspend fun refresh(): Result<Unit> {
        val refreshToken = tokenStore.refreshToken()
            ?: return Result.failure(IllegalStateException("No refresh token available"))
        return runCatching {
            tokenStore.save(api.refresh(RefreshRequest(refreshToken)))
        }
    }

    suspend fun currentUser(): Result<CurrentUserResponse> = runCatching { api.me() }

    fun logout() {
        tokenStore.clear()
    }
}
