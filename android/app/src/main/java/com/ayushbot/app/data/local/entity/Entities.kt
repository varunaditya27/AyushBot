package com.ayushbot.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

// ═══════════════════════════════════════════════════════════════
// Room Database Entities — Local SQLite storage.
// Patient data encrypted at rest via SQLCipher (future).
// ═══════════════════════════════════════════════════════════════

/**
 * PatientEntity — locally stored patient records.
 * ABHA ID optional and locally pseudonymized.
 */
@Entity(tableName = "patients")
data class PatientEntity(
    @PrimaryKey val id: String,           // Local UUID
    val abhaId: String? = null, // Optional ABHA ID (never sent to cloud)
    val name: String? = null, // Optional — privacy sensitive
    val ageMonths: Int,
    val sex: String,          // "Male" / "Female"
    val village: String? = null,
    val ashaId: String,
    val createdAt: Long = System.currentTimeMillis(),
)

/**
 * CaseEntity — individual triage encounter records.
 */
@Entity(tableName = "cases")
data class CaseEntity(
    @PrimaryKey val id: String,           // UUID
    val patientId: String,
    val timestamp: Long = System.currentTimeMillis(),
    val spo2: Float? = null,
    val heartRate: Float? = null,
    val temperature: Float? = null,
    val weight: Float? = null,
    val symptoms: String = "[]",  // JSON array of symptom IDs
    val riskTier: String = "LOW", // LOW, MEDIUM, HIGH, CRITICAL
    val syncStatus: String = "PENDING", // PENDING, SYNCED, FAILED
)

/**
 * RecommendationEntity — AI-generated recommendation for a case.
 */
@Entity(tableName = "recommendations")
data class RecommendationEntity(
    @PrimaryKey val id: String,
    val caseId: String,
    val primaryDiagnosis: String,
    val confidence: String = "Low", // Low, Likely, Confident
    val differentialJson: String = "[]",
    val actionPlan: String = "",
    val referralFacility: String? = null,
    val drugDosage: String? = null,
    val counseling: String? = null,
    val citationSource: String? = null,
    val citationText: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
)

/**
 * FacilityEntity — health facility data for Dijkstra routing.
 */
@Entity(tableName = "facilities")
data class FacilityEntity(
    @PrimaryKey val id: String,
    val name: String,
    val type: String,         // PHC, CHC, DH, SDH
    val latitude: Double,
    val longitude: Double,
    val distanceKm: Float,
    val hasAmbulance: Boolean = false,
)

/**
 * VoiceTurnEntity — locally persisted query/response turns from Voice Query.
 * This keeps the ASHA-facing transcript auditable even when sync is unavailable.
 */
@Entity(tableName = "voice_turns")
data class VoiceTurnEntity(
    @PrimaryKey val id: String,
    val inputText: String,
    val assistantText: String,
    val inputMode: String, // VOICE or TEXT
    val engineUsed: String?,
    val languageId: String,
    val languageTag: String,
    val errorMessage: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val completedAt: Long? = null,
)
