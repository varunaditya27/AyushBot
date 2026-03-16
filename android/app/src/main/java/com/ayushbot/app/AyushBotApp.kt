package com.ayushbot.app

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ayushbot.app.navigation.AyushNavGraph
import com.ayushbot.app.navigation.Screen
import com.ayushbot.app.ui.components.AyushBottomBar
import com.ayushbot.app.ui.components.BottomNavItem
import com.ayushbot.app.ui.theme.AyushBotTheme

// ═══════════════════════════════════════════════════════════════
// AyushBotApp — Root composable.
// Theme + Scaffold + Navigation + Bottom Bar
// ═══════════════════════════════════════════════════════════════

@Composable
fun AyushBotApp() {
    AyushBotTheme {
        val navController = rememberNavController()
        val backStackEntry by navController.currentBackStackEntryAsState()
        val currentRoute = backStackEntry?.destination?.route

        // Show bottom bar only on main screens
        val showBottomBar = currentRoute in listOf(
            Screen.Home.route,
            Screen.CaseHistory.route,
            Screen.Settings.route,
        )

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
                startDestination = Screen.Home.route,
            )
        }
    }
}
