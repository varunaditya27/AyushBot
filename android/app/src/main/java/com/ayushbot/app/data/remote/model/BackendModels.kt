package com.ayushbot.app.data.remote.model

data class HealthResponse(
    val status: String,
    val timestamp: String? = null,
)

data class CaseSummaryResponse(
    val id: String,
    val patientName: String,
    val ageMonths: Int,
    val sex: String,
    val riskTier: String,
    val diagnosis: String? = null,
    val isSynced: Boolean,
    val timestamp: Long,
)

data class CaseCreateRequest(
    val patientName: String,
    val ageMonths: Int,
    val sex: String,
    val vitals: Map<String, Float?>,
    val symptoms: List<String>,
    val ashaId: String,
)

data class CaseCreateResponse(
    val caseId: String,
    val status: String,
)

data class RecommendationResponse(
    val caseId: String,
    val primaryDiagnosis: String,
    val confidence: String,
    val differential: List<String>,
    val actionPlan: String,
    val referralFacility: String? = null,
    val drugDosage: String? = null,
    val counseling: String? = null,
    val citationSource: String? = null,
    val citationText: String? = null,
)
