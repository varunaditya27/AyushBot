package com.ayushbot.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.ayushbot.app.data.local.entity.VoiceTurnEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface VoiceTurnDao {
    @Query("SELECT * FROM voice_turns ORDER BY createdAt DESC")
    fun observeVoiceTurns(): Flow<List<VoiceTurnEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(voiceTurn: VoiceTurnEntity)

    @Query("DELETE FROM voice_turns")
    suspend fun deleteAll()
}
