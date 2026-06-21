package com.ayushbot.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.migration.Migration
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
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
    version = 2,
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
                ).addMigrations(MIGRATION_1_2)
                    .build()
                    .also { instance = it }
            }
        }

        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE patients ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
                db.execSQL("ALTER TABLE patients ADD COLUMN updatedAt INTEGER NOT NULL DEFAULT 0")
                db.execSQL("UPDATE patients SET updatedAt = createdAt WHERE updatedAt = 0")

                db.execSQL("ALTER TABLE cases ADD COLUMN riskExplanation TEXT NOT NULL DEFAULT '{}'")
                db.execSQL("ALTER TABLE cases ADD COLUMN errors TEXT NOT NULL DEFAULT '[]'")
                db.execSQL("ALTER TABLE cases ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
                db.execSQL("ALTER TABLE cases ADD COLUMN updatedAt INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE cases ADD COLUMN rulesetVersion TEXT")
                db.execSQL("ALTER TABLE cases ADD COLUMN growthReferenceVersion TEXT")
                db.execSQL("ALTER TABLE cases ADD COLUMN triageModelVersion TEXT")
                db.execSQL("UPDATE cases SET updatedAt = timestamp WHERE updatedAt = 0")

                db.execSQL("ALTER TABLE recommendations ADD COLUMN citations TEXT NOT NULL DEFAULT '[]'")
                db.execSQL("ALTER TABLE recommendations ADD COLUMN syncStatus TEXT NOT NULL DEFAULT 'PENDING'")
                db.execSQL("ALTER TABLE recommendations ADD COLUMN version INTEGER NOT NULL DEFAULT 1")
                db.execSQL("ALTER TABLE recommendations ADD COLUMN updatedAt INTEGER NOT NULL DEFAULT 0")
                db.execSQL("UPDATE recommendations SET updatedAt = createdAt WHERE updatedAt = 0")
            }
        }
    }
}
