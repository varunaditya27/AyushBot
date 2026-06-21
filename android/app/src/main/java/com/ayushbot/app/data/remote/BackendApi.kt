package com.ayushbot.app.data.remote

import android.content.Context
import com.ayushbot.app.data.remote.model.CurrentUserResponse
import com.ayushbot.app.data.remote.model.DownloadManifest
import com.ayushbot.app.data.remote.model.HealthResponse
import com.ayushbot.app.data.remote.model.LoginRequest
import com.ayushbot.app.data.remote.model.RefreshRequest
import com.ayushbot.app.data.remote.model.SyncBatchRequest
import com.ayushbot.app.data.remote.model.SyncBatchResponse
import com.ayushbot.app.data.remote.model.TelemetryRequest
import com.ayushbot.app.data.remote.model.TelemetryResponse
import com.ayushbot.app.data.remote.model.TokenResponse
import com.ayushbot.app.data.remote.model.TriageAssessmentRequest
import com.ayushbot.app.data.remote.model.TriageAssessmentResponse
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Streaming

interface BackendApi {
    @GET("health/live")
    suspend fun liveness(): HealthResponse

    @GET("health/ready")
    suspend fun readiness(): HealthResponse

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @POST("auth/refresh")
    suspend fun refresh(@Body request: RefreshRequest): TokenResponse

    @GET("auth/me")
    suspend fun me(): CurrentUserResponse

    @POST("sync/upload")
    suspend fun uploadSyncBatch(
        @Header("Idempotency-Key") idempotencyKey: String,
        @Body request: SyncBatchRequest,
    ): SyncBatchResponse

    @GET("sync/manifest")
    suspend fun manifest(): DownloadManifest

    @Streaming
    @GET("sync/resources/{id}")
    suspend fun downloadResource(
        @Path("id") id: String,
        @Header("Range") range: String? = null,
        @Header("If-None-Match") ifNoneMatch: String? = null,
    ): Response<ResponseBody>

    @POST("telemetry")
    suspend fun uploadTelemetry(@Body request: TelemetryRequest): TelemetryResponse

    @POST("triage/assess")
    suspend fun assessTriage(
        @Body request: TriageAssessmentRequest,
    ): TriageAssessmentResponse
}

class AuthTokenStore(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences(
        "ayushbot_auth_tokens",
        Context.MODE_PRIVATE,
    )

    fun accessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)

    fun refreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)

    fun save(tokens: TokenResponse) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, tokens.accessToken)
            .putString(KEY_REFRESH_TOKEN, tokens.refreshToken)
            .apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val KEY_ACCESS_TOKEN = "access_token"
        const val KEY_REFRESH_TOKEN = "refresh_token"
    }
}

private class BearerTokenInterceptor(
    private val tokenStore: AuthTokenStore,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val request = chain.request()
        val token = tokenStore.accessToken()
        if (token.isNullOrBlank() || request.header("Authorization") != null) {
            return chain.proceed(request)
        }
        return chain.proceed(
            request.newBuilder()
                .header("Authorization", "Bearer $token")
                .build(),
        )
    }
}

object BackendApiFactory {
    fun create(baseUrl: String, tokenStore: AuthTokenStore? = null): BackendApi {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val clientBuilder = OkHttpClient.Builder()
            .addInterceptor(logging)
        if (tokenStore != null) {
            clientBuilder.addInterceptor(BearerTokenInterceptor(tokenStore))
        }

        return Retrofit.Builder()
            .baseUrl(normalizeBaseUrl(baseUrl))
            .client(clientBuilder.build())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(BackendApi::class.java)
    }

    private fun normalizeBaseUrl(raw: String): String {
        val trimmed = raw.trim().ifBlank { "http://10.0.2.2:8000/api/v1/" }
        val withSlash = if (trimmed.endsWith("/")) trimmed else "$trimmed/"
        return if (withSlash.endsWith("/api/v1/")) withSlash else "${withSlash}api/v1/"
    }
}
