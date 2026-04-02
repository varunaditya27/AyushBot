package com.ayushbot.app.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf

@Immutable
data class AyushBotMotion(
    val quick: Int = 120,
    val short: Int = 200,
    val medium: Int = 300,
    val long: Int = 450,
    val emphasis: Int = 650,
)

val LocalAyushBotMotion = staticCompositionLocalOf { AyushBotMotion() }
