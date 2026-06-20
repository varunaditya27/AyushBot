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

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(caseEntity: CaseEntity)
}
