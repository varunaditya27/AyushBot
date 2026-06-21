package com.ayushbot.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.ayushbot.app.data.local.entity.CaseEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CaseDao {
    @Query("SELECT * FROM cases ORDER BY timestamp DESC")
    fun observeCases(): Flow<List<CaseEntity>>

    @Query("SELECT * FROM cases WHERE id = :id")
    suspend fun getById(id: String): CaseEntity?

    @Query("SELECT * FROM cases WHERE syncStatus IN ('PENDING', 'FAILED') ORDER BY updatedAt ASC LIMIT :limit")
    suspend fun pendingForSync(limit: Int = 100): List<CaseEntity>

    @Query("UPDATE cases SET syncStatus = :status, version = COALESCE(:serverVersion, version), updatedAt = COALESCE(:serverUpdatedAt, updatedAt) WHERE id = :caseId")
    suspend fun updateSyncStatus(
        caseId: String,
        status: String,
        serverVersion: Int? = null,
        serverUpdatedAt: Long? = null,
    )

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(caseEntity: CaseEntity)
}
