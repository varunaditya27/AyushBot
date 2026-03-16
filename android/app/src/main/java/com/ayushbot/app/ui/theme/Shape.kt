package com.ayushbot.app.ui.theme

import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

// ═══════════════════════════════════════════════════════════════
// AyushBot — Shape System
// Rounded corners signal approachability. Zero radius for
// full-bleed risk banners (importance signal).
// ═══════════════════════════════════════════════════════════════

val AyushBotShapes = Shapes(
    // Text fields, compact chips — conservative
    extraSmall = RoundedCornerShape(4.dp),
    // Filter chips, citation badges
    small = RoundedCornerShape(8.dp),
    // Alert dialogs — formal
    medium = RoundedCornerShape(12.dp),
    // Cards — clearly bounded but not harsh
    large = RoundedCornerShape(16.dp),
    // FAB, bottom sheets — maximum approachability
    extraLarge = RoundedCornerShape(28.dp),
)

// Full pill shape for primary buttons
val PillShape = CircleShape

// Zero radius for risk badge banners (full-bleed importance)
val BannerShape = RoundedCornerShape(0.dp)
