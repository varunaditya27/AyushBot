package com.ayushbot.app.data.remote.model

import com.google.gson.JsonElement
import com.google.gson.annotations.SerializedName

data class HealthResponse(
    val status: String,
    val checks: Map<String, ComponentStatus>? = null,
)

data class ComponentStatus(
    val status: String,
    val required: Boolean,
)

data class LoginRequest(
    val username: String,
    val password: String,
    @SerializedName("device_id") val deviceId: String?,
)

data class RefreshRequest(
    @SerializedName("refresh_token") val refreshToken: String,
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    @SerializedName("token_type") val tokenType: String,
)

data class CurrentUserResponse(
    @SerializedName("user_id") val userId: String,
    val role: String,
    @SerializedName("device_id") val deviceId: String?,
)

data class SyncBatchRequest(
    @SerializedName("idempotency_key") val idempotencyKey: String? = null,
    val records: List<SyncRecord>,
)

data class SyncRecord(
    @SerializedName("client_record_id") val clientRecordId: String,
    val patient: PatientPayload,
    val case: CasePayload,
    val recommendation: RecommendationPayload? = null,
)

data class PatientPayload(
    val id: String,
    @SerializedName("abha_id") val abhaId: String? = null,
    val name: String? = null,
    @SerializedName("age_months") val ageMonths: Int,
    val sex: String,
    val village: String? = null,
    @SerializedName("asha_id") val ashaId: String,
    val version: Int,
    @SerializedName("updated_at") val updatedAt: Long,
)

data class CasePayload(
    val id: String,
    @SerializedName("patient_id") val patientId: String,
    val timestamp: Long,
    val spo2: Float? = null,
    @SerializedName("heart_rate") val heartRate: Float? = null,
    val temperature: Float? = null,
    val weight: Float? = null,
    val symptoms: JsonElement,
    @SerializedName("risk_tier") val riskTier: String,
    @SerializedName("risk_explanation") val riskExplanation: JsonElement,
    val errors: JsonElement,
    @SerializedName("sync_status") val syncStatus: String,
    val version: Int,
    @SerializedName("updated_at") val updatedAt: Long,
    @SerializedName("ruleset_version") val rulesetVersion: String? = null,
    @SerializedName("growth_reference_version") val growthReferenceVersion: String? = null,
    @SerializedName("triage_model_version") val triageModelVersion: String? = null,
)

data class RecommendationPayload(
    val id: String,
    @SerializedName("case_id") val caseId: String,
    @SerializedName("primary_diagnosis") val primaryDiagnosis: String,
    val confidence: String,
    @SerializedName("differential_diagnosis") val differentialDiagnosis: JsonElement,
    @SerializedName("action_plan") val actionPlan: JsonElement,
    val citations: JsonElement,
    @SerializedName("referral_facility") val referralFacility: String? = null,
    @SerializedName("drug_dosage") val drugDosage: String? = null,
    val counseling: String? = null,
    @SerializedName("citation_source") val citationSource: String? = null,
    @SerializedName("citation_text") val citationText: String? = null,
    val version: Int,
    @SerializedName("updated_at") val updatedAt: Long,
)

data class SyncBatchResponse(
    @SerializedName("idempotency_key") val idempotencyKey: String,
    val replayed: Boolean,
    val accepted: Int,
    val rejected: Int,
    val results: List<SyncRecordResult>,
)

data class SyncRecordResult(
    @SerializedName("client_record_id") val clientRecordId: String,
    @SerializedName("patient_id") val patientId: String,
    @SerializedName("case_id") val caseId: String,
    val status: String,
    @SerializedName("server_version") val serverVersion: Int?,
    @SerializedName("server_updated_at") val serverUpdatedAt: Long?,
    @SerializedName("reason_code") val reasonCode: String?,
    val message: String?,
)

data class DownloadManifest(
    @SerializedName("generated_at") val generatedAt: Long,
    @SerializedName("expires_at") val expiresAt: Long,
    val resources: List<ManifestResource>,
    val signature: ManifestSignature,
)

data class ManifestResource(
    val id: String,
    @SerializedName("resource_type") val resourceType: String,
    @SerializedName("resource_id") val resourceId: String,
    val version: Int,
    @SerializedName("download_url") val downloadUrl: String,
    val sha256: String,
    @SerializedName("size_bytes") val sizeBytes: Long,
    @SerializedName("media_type") val mediaType: String,
    val etag: String,
    @SerializedName("published_at") val publishedAt: Long?,
)

data class ManifestSignature(
    val algorithm: String,
    val kid: String,
    val value: String,
)

data class TriageAssessmentRequest(
    @SerializedName("patient_id") val patientId: String? = null,
    @SerializedName("asha_id") val ashaId: String,
    @SerializedName("age_months") val ageMonths: Int,
    val sex: String,
    @SerializedName("village_id") val villageId: String? = null,
    val vitals: Map<String, Float?> = emptyMap(),
    val symptoms: List<String> = emptyList(),
)

data class TriageAssessmentResponse(
    @SerializedName("request_id") val requestId: String,
    @SerializedName("risk_level") val riskLevel: String?,
    @SerializedName("risk_confidence") val riskConfidence: Float?,
    @SerializedName("differential_diagnosis") val differentialDiagnosis: JsonElement?,
    @SerializedName("action_plan") val actionPlan: JsonElement?,
    @SerializedName("asha_output_text") val ashaOutputText: String?,
    @SerializedName("created_at") val createdAt: String,
)

data class TelemetryRequest(
    @SerializedName("event_id") val eventId: String,
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("case_id") val caseId: String? = null,
    @SerializedName("event_type") val eventType: String = "vitals",
    val timestamp: Long,
    val readings: JsonElement,
)

data class TelemetryResponse(
    @SerializedName("event_id") val eventId: String,
    val status: String,
    val persisted: Boolean,
)

data class CaseCreateRequest(
    val patientName: String,
    val ageMonths: Int,
    val sex: String,
    val vitals: Map<String, Float?>,
    val symptoms: List<String>,
    val ashaId: String,
    val village: String? = null,
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
