package com.ayushbot.app.data.repository

import com.ayushbot.app.data.model.TriageCase
import com.ayushbot.app.data.remote.BackendApi
import com.ayushbot.app.data.remote.model.CaseCreateRequest
import com.ayushbot.app.data.remote.model.RecommendationResponse
import com.ayushbot.app.ui.components.RiskTier
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class BackendCaseRepository(
    private val api: BackendApi,
) : CaseRepository {
    override fun observeCases(): Flow<List<TriageCase>> = flow {
        val remoteCases = api.listCases().map { remote ->
            TriageCase(
                id = remote.id,
                patientName = remote.patientName,
                ageMonths = remote.ageMonths,
                sex = remote.sex,
                spo2 = null,
                heartRate = null,
                temperature = null,
                weight = null,
                symptoms = emptyList(),
                riskTier = RiskTier.valueOf(remote.riskTier.uppercase()),
                diagnosis = remote.diagnosis,
                isSynced = remote.isSynced,
                timestamp = remote.timestamp,
            )
        }
        emit(remoteCases)
    }

    override suspend fun submitCase(request: CaseCreateRequest): Result<String> {
        return runCatching { api.submitCase(request).caseId }
    }

    override suspend fun getRecommendation(caseId: String): Result<RecommendationResponse> {
        return runCatching { api.getRecommendation(caseId) }
    }
}
