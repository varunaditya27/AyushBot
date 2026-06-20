package com.ayushbot.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.ayushbot.app.data.local.dao.CaseDao
import com.ayushbot.app.data.local.dao.FacilityDao
import com.ayushbot.app.data.local.dao.PatientDao
import com.ayushbot.app.data.local.dao.RecommendationDao
import com.ayushbot.app.data.local.dao.VoiceTurnDao
import com.ayushbot.app.data.local.entity.CaseEntity
import com.ayushbot.app.data.local.entity.FacilityEntity
import com.ayushbot.app.data.local.entity.PatientEntity
import com.ayushbot.app.data.local.entity.RecommendationEntity
import com.ayushbot.app.data.local.entity.VoiceTurnEntity

@Database(
    entities = [
        PatientEntity::class,
        CaseEntity::class,
        RecommendationEntity::class,
        FacilityEntity::class,
        VoiceTurnEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class AyushBotDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun caseDao(): CaseDao
    abstract fun recommendationDao(): RecommendationDao
    abstract fun facilityDao(): FacilityDao
    abstract fun voiceTurnDao(): VoiceTurnDao

    companion object {
        @Volatile
        private var instance: AyushBotDatabase? = null

        fun getInstance(context: Context): AyushBotDatabase {
            return instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AyushBotDatabase::class.java,
                    "ayushbot.db",
                ).fallbackToDestructiveMigration(dropAllTables = true)
                    .build()
                    .also { instance = it }
            }
        }
    }
}
