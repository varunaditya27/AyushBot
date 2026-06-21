package com.ayushbot.app.data.repository

import com.ayushbot.app.data.model.TriageCase
import com.ayushbot.app.data.remote.model.CaseCreateRequest
import com.ayushbot.app.data.remote.model.RecommendationResponse
import com.ayushbot.app.data.remote.model.SyncBatchResponse
import kotlinx.coroutines.flow.Flow

interface CaseRepository {
    fun observeCases(): Flow<List<TriageCase>>

    suspend fun submitCase(request: CaseCreateRequest): Result<String>

    suspend fun getRecommendation(caseId: String): Result<RecommendationResponse>

    suspend fun syncPending(limit: Int = 100): Result<SyncBatchResponse>
}
