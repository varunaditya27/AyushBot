package com.ayushbot.app.data.repository

import com.ayushbot.app.data.local.dao.CaseDao
import com.ayushbot.app.data.local.dao.PatientDao
import com.ayushbot.app.data.local.dao.RecommendationDao
import com.ayushbot.app.data.local.entity.CaseEntity
import com.ayushbot.app.data.local.entity.PatientEntity
import com.ayushbot.app.data.local.entity.RecommendationEntity
import com.ayushbot.app.data.model.TriageCase
import com.ayushbot.app.data.remote.BackendApi
import com.ayushbot.app.data.remote.model.CaseCreateRequest
import com.ayushbot.app.data.remote.model.CasePayload
import com.ayushbot.app.data.remote.model.PatientPayload
import com.ayushbot.app.data.remote.model.RecommendationPayload
import com.ayushbot.app.data.remote.model.RecommendationResponse
import com.ayushbot.app.data.remote.model.SyncBatchRequest
import com.ayushbot.app.data.remote.model.SyncBatchResponse
import com.ayushbot.app.data.remote.model.SyncRecord
import com.ayushbot.app.ui.components.RiskTier
import com.google.gson.JsonParser
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.util.UUID

class BackendCaseRepository(
    private val api: BackendApi,
    private val patientDao: PatientDao,
    private val caseDao: CaseDao,
    private val recommendationDao: RecommendationDao,
) : CaseRepository {
    override fun observeCases(): Flow<List<TriageCase>> {
        return caseDao.observeCases().map { cases ->
            cases.map { case ->
                case.toTriageCase(recommendation = null)
            }
        }
    }

    override suspend fun submitCase(request: CaseCreateRequest): Result<String> {
        return runCatching {
            val now = System.currentTimeMillis()
            val patientId = UUID.randomUUID().toString()
            val caseId = UUID.randomUUID().toString()
            val recommendationId = UUID.randomUUID().toString()
            val local = evaluateLocalTriage(request)

            patientDao.upsert(
                PatientEntity(
                    id = patientId,
                    name = request.patientName.ifBlank { null },
                    ageMonths = request.ageMonths,
                    sex = request.sex.lowercase(),
                    village = request.village,
                    ashaId = request.ashaId,
                    version = 1,
                    createdAt = now,
                    updatedAt = now,
                )
            )
            caseDao.upsert(
                CaseEntity(
                    id = caseId,
                    patientId = patientId,
                    timestamp = now,
                    spo2 = request.vitals["spo2"],
                    heartRate = request.vitals["heartRate"],
                    temperature = request.vitals["temperature"],
                    weight = request.vitals["weight"],
                    symptoms = toJsonArray(request.symptoms),
                    riskTier = local.riskTier.name,
                    riskExplanation = local.riskExplanationJson,
                    errors = "[]",
                    syncStatus = "PENDING",
                    version = 1,
                    updatedAt = now,
                    rulesetVersion = "android-local-rules-v1",
                    triageModelVersion = "android-deterministic-v1",
                )
            )
            recommendationDao.upsert(
                RecommendationEntity(
                    id = recommendationId,
                    caseId = caseId,
                    primaryDiagnosis = local.primaryDiagnosis,
                    confidence = local.confidence,
                    differentialJson = local.differentialJson,
                    actionPlan = local.actionPlanJson,
                    citations = "[]",
                    counseling = local.counseling,
                    syncStatus = "PENDING",
                    version = 1,
                    createdAt = now,
                    updatedAt = now,
                )
            )
            caseId
        }
    }

    override suspend fun getRecommendation(caseId: String): Result<RecommendationResponse> {
        return runCatching {
            val recommendation = recommendationDao.getByCase(caseId)
                ?: error("Recommendation not found")
            RecommendationResponse(
                caseId = caseId,
                primaryDiagnosis = recommendation.primaryDiagnosis,
                confidence = recommendation.confidence,
                differential = listOf(recommendation.differentialJson),
                actionPlan = recommendation.actionPlan,
                referralFacility = recommendation.referralFacility,
                drugDosage = recommendation.drugDosage,
                counseling = recommendation.counseling,
                citationSource = recommendation.citationSource,
                citationText = recommendation.citationText,
            )
        }
    }

    override suspend fun syncPending(limit: Int): Result<SyncBatchResponse> {
        return runCatching {
            val pendingCases = caseDao.pendingForSync(limit)
            if (pendingCases.isEmpty()) {
                return@runCatching SyncBatchResponse(
                    idempotencyKey = "no-pending-${System.currentTimeMillis()}",
                    replayed = false,
                    accepted = 0,
                    rejected = 0,
                    results = emptyList(),
                )
            }
            val records = pendingCases.mapNotNull { case ->
                val patient = patientDao.getById(case.patientId) ?: return@mapNotNull null
                val recommendation = recommendationDao.getByCase(case.id)
                toSyncRecord(patient, case, recommendation)
            }
            val key = "android-sync-${records.hashCode()}-${records.size}"
            val response = api.uploadSyncBatch(
                idempotencyKey = key,
                request = SyncBatchRequest(idempotencyKey = key, records = records),
            )
            response.results.forEach { result ->
                when (result.status) {
                    "CREATED", "UPDATED", "UNCHANGED" -> {
                        caseDao.updateSyncStatus(
                            caseId = result.caseId,
                            status = "SYNCED",
                            serverVersion = result.serverVersion,
                            serverUpdatedAt = result.serverUpdatedAt,
                        )
                        recommendationDao.updateSyncStatus(
                            caseId = result.caseId,
                            status = "SYNCED",
                            serverVersion = result.serverVersion,
                            serverUpdatedAt = result.serverUpdatedAt,
                        )
                    }
                    "CONFLICT", "REJECTED" -> caseDao.updateSyncStatus(
                        caseId = result.caseId,
                        status = "FAILED",
                    )
                }
            }
            response
        }
    }

    private fun toSyncRecord(
        patient: PatientEntity,
        case: CaseEntity,
        recommendation: RecommendationEntity?,
    ): SyncRecord {
        return SyncRecord(
            clientRecordId = case.id,
            patient = PatientPayload(
                id = patient.id,
                abhaId = patient.abhaId,
                name = patient.name,
                ageMonths = patient.ageMonths,
                sex = patient.sex,
                village = patient.village,
                ashaId = patient.ashaId,
                version = patient.version,
                updatedAt = patient.updatedAt,
            ),
            case = CasePayload(
                id = case.id,
                patientId = case.patientId,
                timestamp = case.timestamp,
                spo2 = case.spo2,
                heartRate = case.heartRate,
                temperature = case.temperature,
                weight = case.weight,
                symptoms = parseJson(case.symptoms),
                riskTier = case.riskTier,
                riskExplanation = parseJson(case.riskExplanation),
                errors = parseJson(case.errors),
                syncStatus = case.syncStatus,
                version = case.version,
                updatedAt = case.updatedAt,
                rulesetVersion = case.rulesetVersion,
                growthReferenceVersion = case.growthReferenceVersion,
                triageModelVersion = case.triageModelVersion,
            ),
            recommendation = recommendation?.let {
                RecommendationPayload(
                    id = it.id,
                    caseId = it.caseId,
                    primaryDiagnosis = it.primaryDiagnosis,
                    confidence = it.confidence,
                    differentialDiagnosis = parseJson(it.differentialJson),
                    actionPlan = parseJson(it.actionPlan),
                    citations = parseJson(it.citations),
                    referralFacility = it.referralFacility,
                    drugDosage = it.drugDosage,
                    counseling = it.counseling,
                    citationSource = it.citationSource,
                    citationText = it.citationText,
                    version = it.version,
                    updatedAt = it.updatedAt,
                )
            },
        )
    }

    private fun CaseEntity.toTriageCase(recommendation: RecommendationEntity?): TriageCase {
        return TriageCase(
            id = id,
            patientName = patientId,
            ageMonths = 0,
            sex = "",
            spo2 = spo2,
            heartRate = heartRate,
            temperature = temperature,
            weight = weight,
            symptoms = symptoms.trim('[', ']').split(",").map { it.trim('"', ' ') }.filter { it.isNotBlank() },
            riskTier = runCatching { RiskTier.valueOf(riskTier) }.getOrDefault(RiskTier.LOW),
            diagnosis = recommendation?.primaryDiagnosis,
            isSynced = syncStatus == "SYNCED",
            timestamp = timestamp,
        )
    }

    private data class LocalTriage(
        val riskTier: RiskTier,
        val primaryDiagnosis: String,
        val confidence: String,
        val riskExplanationJson: String,
        val differentialJson: String,
        val actionPlanJson: String,
        val counseling: String,
    )

    private fun evaluateLocalTriage(request: CaseCreateRequest): LocalTriage {
        val symptoms = request.symptoms.map { it.lowercase() }.toSet()
        val spo2 = request.vitals["spo2"]
        val temperature = request.vitals["temperature"]
        val dangerSigns = listOf(
            "convulsions",
            "unable_drink",
            "lethargic",
            "vomiting",
            "chest_indrawing",
            "stridor",
        ).filter { it in symptoms }
        val risk = when {
            dangerSigns.isNotEmpty() || (spo2 != null && spo2 < 90f) -> RiskTier.CRITICAL
            (spo2 != null && spo2 < 94f) || (temperature != null && temperature >= 39.5f) -> RiskTier.HIGH
            "fast_breathing" in symptoms || "diarrhea" in symptoms -> RiskTier.MEDIUM
            else -> RiskTier.LOW
        }
        val diagnosis = when (risk) {
            RiskTier.CRITICAL -> "Emergency danger signs"
            RiskTier.HIGH -> "High-risk illness"
            RiskTier.MEDIUM -> "Monitor and follow up"
            RiskTier.LOW -> "Low-risk visit"
        }
        val urgency = when (risk) {
            RiskTier.CRITICAL -> "EMERGENCY"
            RiskTier.HIGH -> "SAME_DAY_REFERRAL"
            RiskTier.MEDIUM -> "FOLLOW_UP"
            RiskTier.LOW -> "HOME_CARE"
        }
        return LocalTriage(
            riskTier = risk,
            primaryDiagnosis = diagnosis,
            confidence = if (risk == RiskTier.LOW) "Low" else "Likely",
            riskExplanationJson = """{"source":"android-local-rules-v1","danger_signs":${toJsonArray(dangerSigns)}}""",
            differentialJson = """[{"condition":"$diagnosis","source":"android-local-rules-v1"}]""",
            actionPlanJson = """{"urgency":"$urgency","steps":["Use local approved protocol guidance","Sync when gateway is available"]}""",
            counseling = "This offline recommendation is generated locally and should follow approved ASHA/IMCI guidance.",
        )
    }

    private fun parseJson(raw: String) = JsonParser.parseString(raw)

    private fun toJsonArray(values: List<String>): String {
        return values.joinToString(prefix = "[", postfix = "]") { "\"${it.replace("\"", "\\\"")}\"" }
    }
}
