Here's the complete, grounded mobile app design brainstorm — every screen, every architectural decision, every system interaction, all in plain technical English.

***

# AyushBot Android App — Design Brainstorm Document
## Native Kotlin | Jetpack Compose | Offline-First | BLE + HTTP Sync

***

## 1. Guiding Design Philosophy

Before jumping into screens and flows, three non-negotiable principles must govern every decision:

**Principle 1 — Offline-First, Always.** The app must behave identically with or without network. The UI must never show a spinner waiting for a server. Every action writes to Room (local SQLite) first. The network is a sync mechanism, not a dependency. [linkedin](https://www.linkedin.com/posts/vyanktesh-bargale-mobile-developer_android-systemdesign-offlinefirst-activity-7431685500463239169-DBSL)

**Principle 2 — Low Cognitive Load.** The target user is a woman, often semi-literate in English, conducting 18+ home visits per day in hot weather on a low-end phone. Every screen must have one primary action. No menus deeper than two levels. Icons always accompany text. Forms are structured, not free-form. [mhealth.jmir](https://mhealth.jmir.org/2021/11/e29815)

**Principle 3 — Voice First, Touch Second.** For every major interaction, there must be a voice alternative. An ASHA holding a child should ideally be able to complete a triage without typing anything.

***

## 2. Tech Stack Decisions

### 2.1 UI Layer
**Jetpack Compose (Material Design 3)** is the correct choice for this project — no XML layouts. [developer.android](https://developer.android.com/develop/ui/compose/architecture)

- **State management:** Unidirectional Data Flow (UDF) via Compose's state hoisting. ViewModel holds state, UI renders it. Events bubble up, state flows down.
- **Navigation:** Jetpack Compose Navigation component with a single-activity, multi-screen architecture. Type-safe route definitions.
- **Theming:** Custom Material 3 color scheme built around AyushBot's clinical identity — deep teal primary, amber warning, red critical, green safe. Both light and dark modes.

### 2.2 Architecture Pattern
**Clean Architecture + MVVM** with three strict layers:
- **Data Layer:** Room database as single source of truth. Remote data source as a secondary sync target. Repository pattern abstracts both.
- **Domain Layer:** Use-case classes representing specific business operations (SubmitTriageCase, SyncCasesToGateway, FetchRecommendation, PairSensorPack).
- **Presentation Layer:** Compose screens observe ViewModel state via StateFlow/SharedFlow. No logic in composables.

### 2.3 Offline Sync Architecture
**WorkManager** is the sole mechanism for background sync — it is the only Android API that guarantees deferred execution with retry, network constraints, and battery awareness. [think-it](https://think-it.io/insights/offline-apps)

- Constraint: `NetworkType.CONNECTED` + `RequiresCharging = false`
- Two workers: `SyncCasesWorker` (uploads new cases to gateway when local Wi-Fi detected) and `SyncModelWorker` (downloads updated model weights from gateway)
- Exponential backoff on failure
- Room database stores sync status per case: `PENDING`, `SYNCED`, `FAILED`

### 2.4 BLE Architecture
The BLE stack must run in a foreground service with a persistent notification — Android's requirement for continuous BLE scanning and connection. [developer.android](https://developer.android.com/develop/connectivity/bluetooth/ble/connect-gatt-server)

- `BluetoothLeService` bound service manages the GATT connection lifecycle
- GATT callback events broadcast to the ViewModel via a StateFlow
- BLE connection is NOT required for triage — if sensor pack is absent, ASHA manually enters readings

### 2.5 Local Database Schema (Room)
Five core entities:
- `PatientEntity` — ABHA ID (optional), name, age (months), sex, village, ASHA ID
- `CaseEntity` — Case ID, patient ID, timestamp, vitals snapshot, symptom flags, risk tier, sync status
- `RecommendationEntity` — Case ID, primary diagnosis, differential JSON, action plan, referral slip PDF path
- `FacilityEntity` — Facility graph (nodes + edges) for Dijkstra routing, refreshed on every gateway sync
- `SyncQueueEntity` — Generic sync queue table: payload JSON, endpoint, retry count, status

***

## 3. App Screens — Complete Design

### Screen 1 — Splash & Onboarding (First Launch Only)

A single-time flow across 3 screens:
1. **Language Selection** — Grid of 13 Indian language tiles with script labels and audio preview. ASHA taps her language once. Stored in DataStore Preferences, never asked again.
2. **ASHA Profile Setup** — ASHA ID (from NHM registration), Name, PHC assigned, Village cluster. Optional phone number.
3. **Gateway Pairing** — Stores the PHC gateway HTTP base URL or discovers it on local Wi-Fi when available. Shows "Connected to PHC: Mawlynnong PHC" confirmation or a "Skip — Work Offline" option.

After first launch, this never shows again. App opens directly to the Home Dashboard.

***

### Screen 2 — Home Dashboard

This is the ASHA's operational headquarters. It must be scannable in 2 seconds.

**Top section — Today's summary bar:**
- Cases completed today: `8`
- Pending sync: `3 cases`
- Sensor pack: 🟢 Connected / 🔴 Disconnected / 🟡 Low Battery
- Gateway: 🟢 Connected / 🔴 Offline

**Middle section — Quick Action Buttons (2×2 grid, large touch targets):**
- ➕ New Visit
- 📋 Case History
- 🔊 AyushBot Voice Query (open-ended question to the RAG system without a full case)
- ⚡ Emergency Referral (pre-fills a blank emergency referral slip without triage)

**Bottom section — Recent Cases Feed:**
A scrollable list of today's cases sorted by recency. Each card shows: Patient name (or anonymized ID), timestamp, risk badge color, and primary diagnosis. Tapping opens the full case detail.

**Floating Action Button (FAB):**
A prominent microphone icon labeled "New Visit." Primary entry point for new triage encounters. This is the most-tapped element in the entire app — it must be large, bottom-right, and always visible.

***

### Screen 3 — New Visit Flow (The Core Triage Screen)

This is the most important, most complex screen in the app. It is structured as a **multi-step form wizard** — not a long scrollable form. One step at a time, with a progress stepper at the top.

**Step 1 — Patient Identity**
- Search field: "ABHA ID or Name" — searches local PatientEntity database first. If found, auto-fills demographics (returning patient).
- For new patient: Age in months (number picker with age-group labels: Neonate 0-28 days, Infant 1-12 months, Child 1-5 years), Sex, Village dropdown (pre-populated from ASHA's cluster).
- "Continue" button activates only when age and sex are filled. Name is optional.

**Step 2 — Sensor Capture**
- **If BLE connected:** Live vitals display — three large circular gauges for SpO₂ (red ring), Heart Rate (blue ring), Temperature (orange ring). A "Signal Quality" bar shows reading stability. A pulsing animation plays while readings stabilize. "Record Vitals" button activates only when variance drops below threshold for 5 consecutive readings (this is the signal quality gate). Weight is entered via a number input (from the HX711 LCD readout).
- **If BLE disconnected:** Manual entry mode. Four input fields: SpO₂ %, HR (bpm), Temperature (°C), Weight (kg). A prominent banner: "Sensor pack not connected — manual entry." No silent degradation.
- **TinyML alarm state:** If the sensor pack has raised a hardware danger alarm (communicated via a special BLE GATT characteristic notification), the screen immediately shows a full-width RED banner: "⚠️ SENSOR ALARM — SpO₂ CRITICALLY LOW" before the ASHA even taps anything.

**Step 3 — Symptom Checklist**
A grid of 20 IMCI-derived symptom cards, each with a clear icon, a short label in the ASHA's language, and a binary yes/no toggle. The cards are grouped visually:
- Respiratory group: Fast breathing, Chest indrawing, Stridor at rest
- Danger signs group: Convulsions, Unable to drink/breastfeed, Lethargic/unconscious, Vomiting everything
- Malnutrition group: Severe wasting visible, Bilateral edema, Pallor/severe anemia
- Neonate group: Umbilical redness/pus, Jaundice, Hypothermia
- Fever group: Fever > 7 days, Stiff neck, Runny nose, Measles rash
- Diarrhea group: Diarrhea present, Sunken eyes, Skin pinch very slow

Selected symptoms are visually highlighted. A "Voice Add Symptom" button opens a speech recognition dialog for anything not in the checklist — transcribed by on-device ASR and passed to Agent 5 NER.

**Step 4 — Submit and Wait**
A clean "Analyzing..." screen with a subtle animated waveform. The app computes deterministic triage locally, stores the patient/case/recommendation in Room, and marks the records `PENDING` for later sync. If the gateway is reachable, the app may optionally request a backend enhancement, but the ASHA sees the local recommendation immediately and never waits for a server to receive a diagnostic result.

***

### Screen 4 — AyushBot Recommendation Screen

This is the payoff screen. The ASHA receives her answer here. It must be immediately actionable and emotionally clear.

**Section A — Risk Badge (Full-width, top of screen)**
A large color-coded banner occupying 30% of screen height:
- 🟢 GREEN — "Low Risk: Home Management"
- 🟡 YELLOW — "Monitor: Follow-up in 2 Days"
- 🔴 RED — "Refer: PHC Same Day"
- 🚨 CRITICAL — "EMERGENCY: Call 108 Now" (pulsing red animation, vibration haptic)

**Section B — Primary Diagnosis Card**
A large card with:
- Diagnosis name in the ASHA's language (large, bold)
- Confidence indicator (a simple 3-dot bar: Low / Likely / Confident)
- One-sentence plain-language explanation
- Source citation: "Source: IMCI Pocket Book, Pg. 42" (tap to view the exact protocol passage)

**Section C — What To Do (Action Plan)**
Three expandable cards, collapsed by default for simplicity:
1. **Treat Now:** Drug name, dose, route, duration (e.g., "Amoxicillin syrup — 5 mL every 8 hours for 5 days")
2. **Refer To:** Facility name, distance, estimated travel time, facility type, recommended transport method. A mini-map thumbnail showing the route.
3. **Counsel:** 2-3 plain-language counseling messages to relay to the mother. (e.g., "Continue breastfeeding. Return immediately if breathing becomes worse.")

**Section D — Voice Playback Button**
A large prominent speaker icon at the bottom: "🔊 Read Aloud in [Language]." This plays the AI4Bharat TTS audio of the complete recommendation. This is the most important accessibility feature in the entire app.

**Section E — Referral Slip Button**
"📄 Generate Referral Slip" — creates a formatted PDF pre-filled with patient details, diagnosis, vitals, and receiving facility. Shareable directly via WhatsApp or printable if a nearby Bluetooth printer is available at the PHC.

**Section F — Differential Diagnoses (Collapsed by default)**
An expandable accordion showing the 2 alternative diagnoses with brief explanations. Collapsed because the primary recommendation is what matters most in the field.

***

### Screen 5 — Case History

A searchable, filterable list of all cases stored in Room.

- **Search bar** at the top: searches by patient name, ABHA ID, or diagnosis name
- **Filter chips:** All | Today | This Week | Unsynced | Critical Only
- **Sort options:** Newest first (default), Risk level (Critical first), Alphabetical by patient
- Each card: patient name, age, date, risk badge, primary diagnosis, sync status indicator (🔄 pending / ✅ synced / ⚠️ failed)
- Tapping a case opens the full recommendation detail view (read-only)
- Long-press shows options: Export PDF, Share via WhatsApp, Delete (requires confirmation)

***

### Screen 6 — Voice Query Screen (AyushBot Direct Chat)

This screen allows the ASHA to ask AyushBot a free-standing question without creating a full case record. Use cases: drug dosage questions, protocol clarification, a quick check on a condition she is unsure about.

A simple chat-style interface with:
- A text/voice input bar at the bottom
- Chat bubbles showing ASHA's question and AyushBot's cited response
- Each response bubble shows a small citation chip: "NLEM Pg. 18"
- Conversation is ephemeral (not persisted) unless ASHA taps "Save to Today's Notes"

This is powered by the same EdgeRAG pipeline (Agent 2 only, no triage agents). Latency target: under 3 seconds.

***

### Screen 7 — Sensor Pack Management

Accessed from the Home Dashboard sensor status indicator.

- **Scan and Connect:** A BLE scan result list of nearby devices. AyushBot sensor packs are identified by a custom service UUID prefix shown as "AyushBot Sensor Pack" with MAC address.
- **Live Readings Display:** All four sensors shown continuously — SpO₂, HR, Temp, Weight. A signal quality graph showing the last 30 seconds of SpO₂ variance.
- **TinyML Status:** Shows the current model version on the sensor pack and an "Update Model" button (triggers a firmware OTA via BLE when a newer TinyML model is available from the gateway sync).
- **Battery Level:** Percentage and estimated hours remaining.
- **Calibration Guide:** Step-by-step illustrated guide for correct sensor placement — finger position for oximetry, thermometer placement, zero-tare procedure for weight.

***

### Screen 8 — Settings

Minimal. Only what the ASHA actually needs to configure:
- **Language:** Tap to change app language (triggers Agent 5 language model reload)
- **Gateway:** Current PHC Gateway connection status, option to manually re-scan
- **ASHA Profile:** View and edit name, ID, assigned village cluster
- **Offline Mode Toggle:** Force-offline mode for training or low-battery situations
- **Data Sync Status:** Table showing each category (cases, models, facility graph) with last sync timestamp and size
- **About AyushBot:** Version, open-source license, RVCE affiliation, contact for technical support

***

## 4. Navigation Architecture

The app uses a **bottom navigation bar** for the four primary destinations: Home, New Visit, Case History, Settings. The New Visit destination is the center tab and is visually larger/more prominent than the others.

The complete navigation graph:
```
Root
├── Onboarding Graph (first-launch only)
│   ├── LanguageSelectScreen
│   ├── ASHAProfileSetupScreen
│   └── GatewayPairingScreen
└── Main Graph
    ├── HomeScreen
    ├── NewVisit Graph
    │   ├── PatientIdentityScreen
    │   ├── SensorCaptureScreen
    │   ├── SymptomChecklistScreen
    │   ├── AnalyzingScreen
    │   └── RecommendationScreen
    │       └── ReferralSlipScreen
    ├── CaseHistoryScreen
    │   └── CaseDetailScreen
    ├── VoiceQueryScreen
    ├── SensorManagementScreen
    └── SettingsScreen
```

Back stack is managed cleanly: completing a New Visit clears the 4-screen wizard stack back to Home. Pressing back from Recommendation shows a confirmation dialog ("End this case? Changes will be saved.") before popping.

***

## 5. State Management Architecture

Each screen has a dedicated ViewModel. ViewModels communicate with the data layer only through Use Cases. The state model follows a sealed class pattern: every screen has a `UiState` sealed class with `Loading`, `Success(data)`, and `Error(message)` variants. The Compose UI simply `when`-switches on this sealed class — clean, readable, and testable.

For the BLE sensor stream, a dedicated `SensorViewModel` acts as the single source of truth for live vitals data. It maintains a `Flow<SensorReading>` backed by the `BluetoothLeService` GATT callback. This flow is collected only when the Sensor Capture Screen is visible, preventing battery drain from BLE event processing when the screen is not active.

***

## 6. Key UX/Accessibility Decisions

**Font sizing:** Minimum 16sp body text. 20sp for primary action labels. The app respects system font scale settings.

**Touch targets:** Minimum 48×48dp for all interactive elements, per Material Design 3 accessibility guidelines.

**Color alone is never the only indicator:** Every risk badge (Green/Yellow/Red/Critical) also has a text label and an icon — never purely color-coded, ensuring accessibility for color-blind users.

**Haptic feedback:** The CRITICAL risk badge triggers a strong haptic pulse (VibrationEffect.createWaveform) alongside the visual alarm.

**Timeout handling:** If the app is idle for 5 minutes during an incomplete triage session (ASHA got distracted), the partial case is auto-saved as a Draft in Room. On next launch, a "Resume Draft" banner appears at the top of the Home screen.

**Network status snackbar:** A persistent bottom snackbar ("Working offline — data will sync when connected") appears whenever the app detects no gateway connection. It disappears automatically when the gateway reconnects. This transparent offline communication prevents the ASHA from being confused about why nothing is "sending."

***

## 7. Security and Privacy at the App Layer

- **SQLCipher encryption on Room database:** All patient data at rest is AES-256 encrypted using a key stored in Android Keystore. Even if the phone is physically stolen, patient records are inaccessible without the device unlock. [linkedin](https://www.linkedin.com/posts/vyanktesh-bargale-mobile-developer_android-systemdesign-offlinefirst-activity-7431685500463239169-DBSL)
- **ABHA ID is optional and locally pseudonymized:** If ABHA ID is not provided, the system assigns a local UUID. The ABHA ID is never transmitted to the cloud — only the local UUID travels in FL gradient metadata.
- **Biometric app lock:** Optional biometric (fingerprint) lock on app launch, configurable in Settings.
- **No analytics SDKs:** No Firebase Analytics, no Crashlytics, no third-party tracking. The only telemetry is anonymized aggregate case counts transmitted via the FL sync channel.
- **Referral PDF watermarking:** Generated referral PDFs are watermarked with the ASHA's ID and case timestamp to prevent falsification.

***

## 8. What Makes This App Research-Worthy

The app itself generates several measurable research metrics for the paper:

- **System Usability Scale (SUS):** 10-item survey administered to ASHAs in the pilot. Target: SUS > 70.
- **Task Completion Rate:** % of triage sessions reaching the Recommendation screen without abandonment. Target: > 85%.
- **Time-on-Task:** Median time from tapping "New Visit" to seeing the Recommendation screen. Target: < 5 minutes.
- **Voice vs. Touch usage split:** What proportion of symptom entry uses voice input vs. checklist? This informs multilingual NLP training priorities.
- **Offline operation rate:** What % of cases are submitted while the gateway is unreachable, testing the offline-first architecture?

These metrics all feed directly into the user study section of the research paper, making the app not just a product but a controlled experiment platform.

***

## Key Open Design Questions for the Team to Decide

Three decisions that significantly affect implementation complexity and should be settled now:

1. **Checklist vs. Voice as Primary:** Should the symptom step default to the checklist (structured, faster) or the voice input (richer, harder to implement reliably)? Recommendation: default to checklist with voice as a supplement, based on documented ASHA usability research.

2. **On-Device vs. Gateway Fallback Triage:** When the gateway is unreachable, should the phone run a minimal local rule-based triage (fast, deterministic, no LLM) or silently queue and wait? Recommendation: show the rule-based result immediately and update it when the gateway responds, similar to optimistic UI update patterns. [developer.android](https://developer.android.com/topic/architecture/data-layer/offline-first)

3. **Referral Slip Format:** WhatsApp-shareable image vs. PDF vs. plain text. PDF is most professional but requires a PDF library. WhatsApp-shared image is most practical given that most Indian district hospital staff use WhatsApp. Recommendation: generate both — a formatted image for immediate WhatsApp sharing and a PDF for archival.
