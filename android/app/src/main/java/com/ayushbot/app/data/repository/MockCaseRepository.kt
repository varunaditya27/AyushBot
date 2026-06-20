package com.ayushbot.app.data.repository

import com.ayushbot.app.data.model.TriageCase
import com.ayushbot.app.data.remote.model.CaseCreateRequest
import com.ayushbot.app.data.remote.model.RecommendationResponse
import com.ayushbot.app.ui.components.RiskTier
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import java.util.UUID

class MockCaseRepository : CaseRepository {
    private val cases = MutableStateFlow(sampleCases())

    override fun observeCases(): Flow<List<TriageCase>> = cases

    override suspend fun submitCase(request: CaseCreateRequest): Result<String> {
        val caseId = UUID.randomUUID().toString()
        val newCase = TriageCase(
            id = caseId,
            patientName = request.patientName,
            ageMonths = request.ageMonths,
            sex = request.sex,
            spo2 = request.vitals["spo2"],
            heartRate = request.vitals["heartRate"],
            temperature = request.vitals["temperature"],
            weight = request.vitals["weight"],
            symptoms = request.symptoms,
            riskTier = RiskTier.MEDIUM,
            diagnosis = null,
            isSynced = false,
            timestamp = System.currentTimeMillis(),
        )
        cases.value = listOf(newCase) + cases.value
        return Result.success(caseId)
    }

    override suspend fun getRecommendation(caseId: String): Result<RecommendationResponse> {
        return Result.success(
            RecommendationResponse(
                caseId = caseId,
                primaryDiagnosis = "Acute watery diarrhea",
                confidence = "Likely",
                differential = listOf("Viral gastroenteritis", "Food-borne illness"),
                actionPlan = "Start ORS and monitor hydration. Refer if danger signs present.",
                referralFacility = "Mawlynnong PHC",
                drugDosage = "ORS 75 mL/kg over 4 hours",
                counseling = "Continue breastfeeding and offer zinc for 14 days.",
                citationSource = "IMCI Chart Booklet",
                citationText = "Section 5, p. 78",
            )
        )
    }

    private fun sampleCases(): List<TriageCase> = listOf(
        TriageCase(
            id = "case-101",
            patientName = "Anaya Sharma",
            ageMonths = 26,
            sex = "Female",
            spo2 = 96f,
            heartRate = 118f,
            temperature = 37.9f,
            weight = 11.2f,
            symptoms = listOf("Loose stools", "Mild fever"),
            riskTier = RiskTier.MEDIUM,
            diagnosis = "Acute watery diarrhea",
            isSynced = true,
            timestamp = System.currentTimeMillis() - 86_400_000,
        ),
        TriageCase(
            id = "case-102",
            patientName = "Rohit Das",
            ageMonths = 10,
            sex = "Male",
            spo2 = 92f,
            heartRate = 146f,
            temperature = 38.6f,
            weight = 7.9f,
            symptoms = listOf("Fast breathing", "Cough"),
            riskTier = RiskTier.HIGH,
            diagnosis = "Severe pneumonia",
            isSynced = false,
            timestamp = System.currentTimeMillis() - 4_200_000,
        ),
    )
}
