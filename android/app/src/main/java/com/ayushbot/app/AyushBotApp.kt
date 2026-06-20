package com.ayushbot.app

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ayushbot.app.core.di.LocalAppContainer
import com.ayushbot.app.navigation.AyushNavGraph
import com.ayushbot.app.navigation.Screen
import com.ayushbot.app.ui.components.AyushBottomBar
import com.ayushbot.app.ui.components.BottomNavItem
import com.ayushbot.app.ui.theme.AyushBotTheme

private const val PREFS_NAME = "ayushbot_prefs"
private const val KEY_ONBOARDING_DONE = "onboarding_done"

// ═══════════════════════════════════════════════════════════════
// AyushBotApp — Root composable.
// Theme + Scaffold + Navigation + Bottom Bar
// Onboarding shown only on first launch (via SharedPreferences).
// ═══════════════════════════════════════════════════════════════

@Composable
fun AyushBotApp() {
    AyushBotTheme {
        val context = LocalContext.current
        val appContainer = (context.applicationContext as AyushBotApplication).appContainer

        // Determine start destination based on first-launch state
        val startDestination = remember {
            val prefs = context.getSharedPreferences(PREFS_NAME, android.content.Context.MODE_PRIVATE)
            if (prefs.getBoolean(KEY_ONBOARDING_DONE, false)) {
                Screen.Home.route
            } else {
                Screen.Onboarding.route
            }
        }

        val navController = rememberNavController()
        val backStackEntry by navController.currentBackStackEntryAsState()
        val currentRoute = backStackEntry?.destination?.route

        // Show bottom bar only on main screens
        val showBottomBar = currentRoute in listOf(
            Screen.Home.route,
            Screen.CaseHistory.route,
            Screen.Settings.route,
        )

        CompositionLocalProvider(LocalAppContainer provides appContainer) {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                bottomBar = {
                    if (showBottomBar) {
                        AyushBottomBar(
                            currentRoute = currentRoute,
                            onNavigate = { item ->
                                val route = when (item) {
                                    BottomNavItem.HOME -> Screen.Home.route
                                    BottomNavItem.NEW_VISIT -> Screen.NewVisit.route
                                    BottomNavItem.HISTORY -> Screen.CaseHistory.route
                                    BottomNavItem.SETTINGS -> Screen.Settings.route
                                }
                                navController.navigate(route) {
                                    popUpTo(Screen.Home.route) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                        )
                    }
                },
            ) { innerPadding ->
                AyushNavGraph(
                    navController = navController,
                    startDestination = startDestination,
                    onOnboardingComplete = {
                        // Mark onboarding done so it won't show again
                        context.getSharedPreferences(PREFS_NAME, android.content.Context.MODE_PRIVATE)
                            .edit()
                            .putBoolean(KEY_ONBOARDING_DONE, true)
                            .apply()
                    },
                    modifier = Modifier.padding(innerPadding),
                )
            }
        }
    }
}
