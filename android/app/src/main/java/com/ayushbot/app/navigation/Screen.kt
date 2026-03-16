package com.ayushbot.app.navigation

// ═══════════════════════════════════════════════════════════════
// Screen — Sealed class defining all navigation destinations.
// Type-safe route definitions for Compose Navigation.
// ═══════════════════════════════════════════════════════════════

sealed class Screen(val route: String) {
    // Onboarding (first-launch only)
    data object Onboarding : Screen("onboarding")

    // Main graph destinations
    data object Home : Screen("home")
    data object NewVisit : Screen("new_visit")
    data object Recommendation : Screen("recommendation")
    data object CaseHistory : Screen("history")
    data object CaseDetail : Screen("case_detail/{caseId}") {
        fun createRoute(caseId: String) = "case_detail/$caseId"
    }
    data object VoiceQuery : Screen("voice_query")
    data object Settings : Screen("settings")
    data object SensorManagement : Screen("sensor_management")
}
