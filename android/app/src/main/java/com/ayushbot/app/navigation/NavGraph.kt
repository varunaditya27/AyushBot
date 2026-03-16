package com.ayushbot.app.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.ayushbot.app.ui.screens.*

// ═══════════════════════════════════════════════════════════════
// AyushNavGraph — Compose Navigation graph.
// Onboarding sub-graph (first-launch) + Main sub-graph.
// ═══════════════════════════════════════════════════════════════

@Composable
fun AyushNavGraph(
    navController: NavHostController,
    startDestination: String = Screen.Home.route,
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
    ) {
        // ─── Onboarding ───
        composable(Screen.Onboarding.route) {
            OnboardingScreen(
                onComplete = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Onboarding.route) { inclusive = true }
                    }
                }
            )
        }

        // ─── Home Dashboard ───
        composable(Screen.Home.route) {
            HomeScreen(
                onNewVisit = { navController.navigate(Screen.NewVisit.route) },
                onCaseHistory = { navController.navigate(Screen.CaseHistory.route) },
                onVoiceQuery = { navController.navigate(Screen.VoiceQuery.route) },
                onSettings = { navController.navigate(Screen.Settings.route) },
            )
        }

        // ─── New Visit Wizard ───
        composable(Screen.NewVisit.route) {
            NewVisitScreen(
                onBack = { navController.popBackStack() },
                onComplete = {
                    navController.navigate(Screen.Recommendation.route) {
                        popUpTo(Screen.NewVisit.route) { inclusive = true }
                    }
                },
            )
        }

        // ─── Recommendation ───
        composable(Screen.Recommendation.route) {
            RecommendationScreen(
                onBack = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Home.route) { inclusive = true }
                    }
                },
            )
        }

        // ─── Case History ───
        composable(Screen.CaseHistory.route) {
            CaseHistoryScreen(
                onCaseClick = { caseId ->
                    navController.navigate(Screen.Recommendation.route)
                },
            )
        }

        // ─── Voice Query ───
        composable(Screen.VoiceQuery.route) {
            VoiceQueryScreen(
                onBack = { navController.popBackStack() },
            )
        }

        // ─── Settings ───
        composable(Screen.Settings.route) {
            SettingsScreen()
        }
    }
}
