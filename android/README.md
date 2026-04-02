<!-- markdownlint-disable MD033 MD036 MD041 -->

<div align="center">

# 📱 AyushBot Android Client

**Offline-First Native Android Interface for ASHA Workers**

</div>

## 📌 Canonical Design References

Frontend implementation in this module follows these two canonical documents:

- `android/docs/ayushbot-design-specs-legendary.md` (**implementation authority**)
- `android/docs/ayushbot-branding-guide-legendary.md` (**brand/voice authority**)

If any UI behavior conflicts with earlier docs, follow the **legendary** documents.

---

## 🧭 Frontend Architecture (Current)

The Android app is implemented in **Kotlin + Jetpack Compose (Material 3)** with an offline-first design contract.

### UI layers in this module

- `ui/theme/` → color, typography, shape, spacing, motion, semantics primitives
- `ui/components/` → reusable components (`RiskBadge`, `VitalGauge`, `ActionPlanCard`, `VoicePlaybackButton`, etc.)
- `ui/screens/` → screen implementations and UI-state handling (`ScreenUiState`, `VoiceMicState`, `SyncState`)
- `navigation/` → route graph and destination wiring

### Layout safety foundations

- Root scaffold insets are propagated into `NavHost` content to prevent bottom bar overlap.
- Reusable spacing/motion primitives are centralized (`Spacing.kt`, `Motion.kt`).
- Accessibility semantics helpers are centralized (`Semantics.kt`).

---

## 🎨 Design System Implementation

### Color and risk semantics

- Material 3 static color schemes are used (dynamic color intentionally disabled for clinical safety).
- Clinical risk semantics are invariant and non-decorative:
  - Safe: `#1B6E2C`
  - Monitor: `#B45309`
  - High: `#C2410C`
  - Critical: `#9B1C1C`

### Typography

- Primary: Noto Sans
- Evidence/citation text: Noto Serif
- Numeric vitals: JetBrains Mono
- Locale-aware line-height helper exists for script-specific readability.

### Spacing + touch targets

- 4dp base grid with tokens (`xs`→`xxl`) in `Spacing.kt`
- Minimum touch targets: 48×48dp
- Fixed-height high-risk components were replaced with bounded/adaptive sizing where required.

---

## 🧩 Screen Catalog (Implemented)

### 1) Onboarding

- language selection (adaptive grid)
- ASHA profile setup
- gateway pairing

### 2) Home

- today summary
- quick actions
- recent cases list
- state handling: loading / empty / error / offline
- critical-pending strip for urgent follow-ups

### 3) New Visit Wizard

- step flow: Patient → Vitals → Symptoms → Analyzing
- quality-gated sensor capture
- responsive symptom grid
- validation-gated progression

### 4) Recommendation

- hierarchy: Risk Badge → Primary Diagnosis → Action Plan → Evidence → Voice CTA
- state handling: loading / empty / error / offline
- low-confidence warning behavior

### 5) Case History

- search + filter chips (horizontally scrollable)
- explicit sync-status chips on cards
- state handling: loading / empty / error / offline

### 6) Voice Query

- chat interface with citation chips
- voice state machine: idle / listening / processing / error
- keyboard-safe bottom input bar and responsive chat bubble widths

### 7) Settings

- profile and connection sections
- local-save feedback for toggle settings
- route into Sensor Management

### 8) Sensor Management

- sensor connection status
- live gauges
- signal-quality diagnostics
- self-test and calibration affordances

---

## ♿ Accessibility & Clean Layout Guarantees

Current frontend implementation enforces:

- no meaning by color alone for clinical risk
- responsive/bounded component sizing for larger font scales
- reduced nested padding conflicts in key screens
- keyboard + navigation bar inset handling for input screens
- reusable semantic helpers for headings and live-region alerts

Recommended manual checks before release:

- TalkBack traversal on Home/New Visit/Recommendation/Voice Query
- large-font checks (1.3x / 1.5x)
- portrait + landscape overlap checks on small and medium devices

---

## 🔄 Offline-First UX Behavior

UI explicitly surfaces connectivity context:

- offline banners/cards in stateful screens
- pending/synced status visibility in history/home
- local-first behavior in voice and recommendation flows when online resources are unavailable

---

## 🛠️ Build & Test

From `android/`:

- Build debug APK: `./gradlew assembleDebug`
- Install debug APK: `./gradlew installDebug`
- Unit tests: `./gradlew testDebugUnitTest`

For UI verification, run app on emulator/physical device and validate the state matrix behavior on each major screen.

---

## 📎 Key Frontend Paths

- `app/src/main/java/com/ayushbot/app/AyushBotApp.kt`
- `app/src/main/java/com/ayushbot/app/navigation/NavGraph.kt`
- `app/src/main/java/com/ayushbot/app/ui/theme/`
- `app/src/main/java/com/ayushbot/app/ui/components/`
- `app/src/main/java/com/ayushbot/app/ui/screens/`
