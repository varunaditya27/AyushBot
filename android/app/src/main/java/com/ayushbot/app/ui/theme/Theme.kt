package com.ayushbot.app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.LocalContext
import androidx.core.view.WindowCompat

// ═══════════════════════════════════════════════════════════════
// AyushBot — Material 3 Theme
// Dynamic Color EXPLICITLY DISABLED for clinical safety.
// Risk state colors must remain invariant regardless of wallpaper.
// ═══════════════════════════════════════════════════════════════

private val LightColorScheme = lightColorScheme(
    primary = PrimaryLight,
    onPrimary = OnPrimaryLight,
    primaryContainer = PrimaryContainerLight,
    onPrimaryContainer = OnPrimaryContainerLight,
    secondary = SecondaryLight,
    onSecondary = OnSecondaryLight,
    secondaryContainer = SecondaryContainerLight,
    onSecondaryContainer = OnSecondaryContainerLight,
    tertiary = TertiaryLight,
    onTertiary = OnTertiaryLight,
    tertiaryContainer = TertiaryContainerLight,
    onTertiaryContainer = OnTertiaryContainerLight,
    error = ErrorLight,
    onError = OnErrorLight,
    errorContainer = ErrorContainerLight,
    onErrorContainer = OnErrorContainerLight,
    background = BackgroundLight,
    onBackground = OnSurfaceLight,
    surface = SurfaceLight,
    onSurface = OnSurfaceLight,
    surfaceVariant = SurfaceVariantLight,
    onSurfaceVariant = OnSurfaceVariantLight,
    outline = OutlineLight,
    outlineVariant = OutlineVariantLight,
    inverseSurface = InverseSurfaceLight,
    inverseOnSurface = InverseOnSurfaceLight,
    inversePrimary = InversePrimaryLight,
    surfaceContainerLow = SurfaceContainerLowLight,
    surfaceContainer = SurfaceContainerLight,
    surfaceContainerHigh = SurfaceContainerHighLight,
)

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryDark,
    onPrimary = OnPrimaryDark,
    primaryContainer = PrimaryContainerDark,
    onPrimaryContainer = OnPrimaryContainerDark,
    secondary = SecondaryDark,
    onSecondary = OnSecondaryDark,
    secondaryContainer = SecondaryContainerDark,
    onSecondaryContainer = OnSecondaryContainerDark,
    tertiary = TertiaryDark,
    onTertiary = OnTertiaryDark,
    tertiaryContainer = TertiaryContainerDark,
    onTertiaryContainer = OnTertiaryContainerDark,
    error = ErrorDark,
    onError = OnErrorDark,
    errorContainer = ErrorContainerDark,
    onErrorContainer = OnErrorContainerDark,
    background = BackgroundDark,
    onBackground = OnSurfaceDark,
    surface = SurfaceDark,
    onSurface = OnSurfaceDark,
    surfaceVariant = SurfaceVariantDark,
    onSurfaceVariant = OnSurfaceVariantDark,
    outline = OutlineDark,
    outlineVariant = OutlineVariantDark,
    inverseSurface = InverseSurfaceDark,
    inverseOnSurface = InverseOnSurfaceDark,
    inversePrimary = InversePrimaryDark,
    surfaceContainerLow = SurfaceContainerLowDark,
    surfaceContainer = SurfaceContainerDark,
    surfaceContainerHigh = SurfaceContainerHighDark,
)

@Composable
fun AyushBotTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.surface.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    val context = LocalContext.current
    val currentMultiplier = androidx.compose.runtime.remember(context) {
        val prefs = context.getSharedPreferences("ayushbot_prefs", android.content.Context.MODE_PRIVATE)
        val selectedLanguage = prefs.getString("selected_language", null)
            ?: java.util.Locale.getDefault().language
        lineHeightMultiplierForLanguage(selectedLanguage)
    }
    val localeTypography = androidx.compose.runtime.remember(currentMultiplier) {
        androidx.compose.material3.Typography(
            displayLarge = AyushBotTypography.displayLarge.withLocaleAwareLineHeight(currentMultiplier),
            displayMedium = AyushBotTypography.displayMedium.withLocaleAwareLineHeight(currentMultiplier),
            displaySmall = AyushBotTypography.displaySmall.withLocaleAwareLineHeight(currentMultiplier),
            headlineLarge = AyushBotTypography.headlineLarge.withLocaleAwareLineHeight(currentMultiplier),
            headlineMedium = AyushBotTypography.headlineMedium.withLocaleAwareLineHeight(currentMultiplier),
            headlineSmall = AyushBotTypography.headlineSmall.withLocaleAwareLineHeight(currentMultiplier),
            titleLarge = AyushBotTypography.titleLarge.withLocaleAwareLineHeight(currentMultiplier),
            titleMedium = AyushBotTypography.titleMedium.withLocaleAwareLineHeight(currentMultiplier),
            titleSmall = AyushBotTypography.titleSmall.withLocaleAwareLineHeight(currentMultiplier),
            bodyLarge = AyushBotTypography.bodyLarge.withLocaleAwareLineHeight(currentMultiplier),
            bodyMedium = AyushBotTypography.bodyMedium.withLocaleAwareLineHeight(currentMultiplier),
            bodySmall = AyushBotTypography.bodySmall.withLocaleAwareLineHeight(currentMultiplier),
            labelLarge = AyushBotTypography.labelLarge.withLocaleAwareLineHeight(currentMultiplier),
            labelMedium = AyushBotTypography.labelMedium.withLocaleAwareLineHeight(currentMultiplier),
            labelSmall = AyushBotTypography.labelSmall.withLocaleAwareLineHeight(currentMultiplier),
        )
    }

    CompositionLocalProvider(
        LocalAyushBotSpacing provides AyushBotSpacing(),
        LocalAyushBotMotion provides AyushBotMotion(),
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = localeTypography,
            shapes = AyushBotShapes,
            content = content,
        )
    }
}

object AyushBotDesignSystem {
    val spacing: AyushBotSpacing
        @Composable get() = LocalAyushBotSpacing.current

    val motion: AyushBotMotion
        @Composable get() = LocalAyushBotMotion.current
}
