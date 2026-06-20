package com.ayushbot.app.data.remote

import com.ayushbot.app.data.remote.model.CaseCreateRequest
import com.ayushbot.app.data.remote.model.CaseCreateResponse
import com.ayushbot.app.data.remote.model.CaseSummaryResponse
import com.ayushbot.app.data.remote.model.HealthResponse
import com.ayushbot.app.data.remote.model.RecommendationResponse
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface BackendApi {
    @GET("health")
    suspend fun health(): HealthResponse

    @GET("cases")
    suspend fun listCases(): List<CaseSummaryResponse>

    @POST("cases")
    suspend fun submitCase(@Body request: CaseCreateRequest): CaseCreateResponse

    @GET("cases/{caseId}/recommendation")
    suspend fun getRecommendation(@Path("caseId") caseId: String): RecommendationResponse
}

object BackendApiFactory {
    fun create(baseUrl: String): BackendApi {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(BackendApi::class.java)
    }
}
