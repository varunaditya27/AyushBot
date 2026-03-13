# =============================================================================
# AyushBot Backend — Database Models (SQLAlchemy ORM)
# =============================================================================
#
# PURPOSE:
#   Defines the SQLAlchemy ORM models that represent all persistent data
#   tables on the PHC gateway's local SQLite database.
#
# TABLES:
#
#   patients
#     Stores patient demographic records.
#     - id: UUID primary key
#     - abha_id: Optional ABHA (Ayushman Bharat Health Account) identifier
#     - name: Encrypted patient name (ASCON-128 or AES-256 at rest)
#     - age_months: Integer
#     - sex: Enum (MALE, FEMALE, OTHER)
#     - village_id: Foreign key to villages table
#     - created_at: Timestamp
#     - updated_at: Timestamp
#     NOTE: Patient names and identifiers are encrypted at rest using the
#     gateway's device key. Only the gateway process can decrypt them.
#
#   encounters
#     Stores individual triage encounters (one per ASHA visit per patient).
#     - id: UUID primary key
#     - patient_id: Foreign key to patients
#     - asha_id: String (ASHA worker identifier)
#     - timestamp: When the encounter occurred
#     - raw_vitals: JSON blob of sensor readings
#     - validated_vitals: JSON blob of quality-checked vitals
#     - risk_level: Enum (LOW, MEDIUM, HIGH, CRITICAL)
#     - risk_confidence: Float
#     - differential_diagnosis: JSON blob (Agent 2 output)
#     - action_plan: JSON blob (Agent 3 output)
#     - asha_input_text: Original ASHA input (local language)
#     - translated_symptoms: Standardized English symptoms
#     - pipeline_duration_ms: Total agent pipeline execution time
#     - agent_timings: JSON blob of per-agent durations
#     - created_at: Timestamp
#
#   outcomes
#     Stores feedback from the PHC Medical Officer (ground truth labels).
#     - id: UUID primary key
#     - encounter_id: Foreign key to encounters
#     - confirmed_diagnosis: String (doctor's confirmed diagnosis)
#     - doctor_notes: Text (optional clinical notes)
#     - outcome_date: Timestamp
#     - used_for_fl: Boolean (whether this label has been used in FL training)
#
#   fl_training_log
#     Stores records of local FL training rounds.
#     - id: UUID primary key
#     - round_number: Integer (monotonically increasing)
#     - started_at: Timestamp
#     - completed_at: Timestamp
#     - samples_used: Integer
#     - epochs: Integer
#     - loss_history: JSON array of per-epoch loss values
#     - dp_epsilon_spent: Float (privacy budget consumed in this round)
#     - cumulative_epsilon: Float (total privacy budget consumed to date)
#     - gradient_size_bytes: Integer
#     - sync_status: Enum (PENDING, UPLOADED, FAILED)
#     - synced_at: Optional Timestamp
#
#   villages
#     Static reference data for geographic routing.
#     - id: String primary key (village code)
#     - name: String
#     - district: String
#     - nearest_phc: String (facility code)
#     - gps_lat: Float
#     - gps_lng: Float
#
#   facilities
#     Static reference data for referral destinations.
#     - id: String primary key (facility code)
#     - name: String
#     - facility_type: Enum (PHC, CHC, DH)
#     - address: String
#     - phone: Optional String
#     - gps_lat: Float
#     - gps_lng: Float
#
# INDEXING:
#   - encounters: index on (patient_id, timestamp) for history queries
#   - encounters: index on (asha_id, timestamp) for per-ASHA queries
#   - fl_training_log: index on (sync_status) for pending upload queries
#
# DATA RETENTION:
#   Data is retained locally for 2 years per DPDPA 2023 requirements, then
#   archived (encrypted export to SD card) and purged from the active database.
# =============================================================================
