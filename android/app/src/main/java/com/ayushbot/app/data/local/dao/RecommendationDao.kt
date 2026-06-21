package com.ayushbot.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.ayushbot.app.data.local.entity.RecommendationEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface RecommendationDao {
    @Query("SELECT * FROM recommendations WHERE caseId = :caseId LIMIT 1")
    fun observeByCase(caseId: String): Flow<RecommendationEntity?>

    @Query("SELECT * FROM recommendations WHERE caseId = :caseId LIMIT 1")
    suspend fun getByCase(caseId: String): RecommendationEntity?

    @Query("UPDATE recommendations SET syncStatus = :status, version = COALESCE(:serverVersion, version), updatedAt = COALESCE(:serverUpdatedAt, updatedAt) WHERE caseId = :caseId")
    suspend fun updateSyncStatus(
        caseId: String,
        status: String,
        serverVersion: Int? = null,
        serverUpdatedAt: Long? = null,
    )

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(recommendation: RecommendationEntity)
}
