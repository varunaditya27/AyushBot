package com.ayushbot.app.ui.theme

import androidx.compose.ui.graphics.Color

// ═══════════════════════════════════════════════════════════════
// AyushBot — Material 3 Color System
// Seed: Teal (H:186° C:40 T:35) • Saffron • Forest Green
// ═══════════════════════════════════════════════════════════════

// ─── Primary: Clinical Teal ───
val PrimaryLight = Color(0xFF006874)
val OnPrimaryLight = Color(0xFFFFFFFF)
val PrimaryContainerLight = Color(0xFF97F0FF)
val OnPrimaryContainerLight = Color(0xFF001F24)

// ─── Secondary: Muted Teal ───
val SecondaryLight = Color(0xFF4A6267)
val OnSecondaryLight = Color(0xFFFFFFFF)
val SecondaryContainerLight = Color(0xFFCCE8ED)
val OnSecondaryContainerLight = Color(0xFF051F23)

// ─── Tertiary: Warm Saffron ───
val TertiaryLight = Color(0xFF7D5700)
val OnTertiaryLight = Color(0xFFFFFFFF)
val TertiaryContainerLight = Color(0xFFFFDDB3)
val OnTertiaryContainerLight = Color(0xFF281900)

// ─── Error: Deep Red ───
val ErrorLight = Color(0xFFBA1A1A)
val OnErrorLight = Color(0xFFFFFFFF)
val ErrorContainerLight = Color(0xFFFFDAD6)
val OnErrorContainerLight = Color(0xFF410002)

// ─── Surfaces (Light) ───
val BackgroundLight = Color(0xFFFAFDFD)
val SurfaceLight = Color(0xFFFAFDFD)
val SurfaceVariantLight = Color(0xFFDBE4E6)
val OnSurfaceLight = Color(0xFF191C1D)
val OnSurfaceVariantLight = Color(0xFF3F484A)
val OutlineLight = Color(0xFF6F797A)
val OutlineVariantLight = Color(0xFFBFC8CA)
val SurfaceContainerLight = Color(0xFFEEF1F2)
val SurfaceContainerHighLight = Color(0xFFE8ECEC)
val SurfaceContainerLowLight = Color(0xFFF4F7F7)
val InverseSurfaceLight = Color(0xFF2E3132)
val InverseOnSurfaceLight = Color(0xFFEFF1F1)
val InversePrimaryLight = Color(0xFF4FD8EB)

// ═══════════════════════════════════════════════════════════════
// Dark Mode Palette
// ═══════════════════════════════════════════════════════════════

// ─── Primary: Bright Teal on Dark ───
val PrimaryDark = Color(0xFF4FD8EB)
val OnPrimaryDark = Color(0xFF00363D)
val PrimaryContainerDark = Color(0xFF004F58)
val OnPrimaryContainerDark = Color(0xFF97F0FF)

// ─── Secondary ───
val SecondaryDark = Color(0xFFB1CBD0)
val OnSecondaryDark = Color(0xFF1C3438)
val SecondaryContainerDark = Color(0xFF334B4F)
val OnSecondaryContainerDark = Color(0xFFCCE8ED)

// ─── Tertiary ───
val TertiaryDark = Color(0xFFF5BE48)
val OnTertiaryDark = Color(0xFF422D00)
val TertiaryContainerDark = Color(0xFF5F4100)
val OnTertiaryContainerDark = Color(0xFFFFDDB3)

// ─── Error ───
val ErrorDark = Color(0xFFFFB4AB)
val OnErrorDark = Color(0xFF690005)
val ErrorContainerDark = Color(0xFF93000A)
val OnErrorContainerDark = Color(0xFFFFDAD6)

// ─── Surfaces (Dark) ───
val BackgroundDark = Color(0xFF191C1D)
val SurfaceDark = Color(0xFF191C1D)
val SurfaceVariantDark = Color(0xFF3F484A)
val OnSurfaceDark = Color(0xFFE1E3E3)
val OnSurfaceVariantDark = Color(0xFFBFC8CA)
val OutlineDark = Color(0xFF899294)
val OutlineVariantDark = Color(0xFF3F484A)
val SurfaceContainerDark = Color(0xFF1D2021)
val SurfaceContainerHighDark = Color(0xFF282B2C)
val SurfaceContainerLowDark = Color(0xFF191C1D)
val InverseSurfaceDark = Color(0xFFE1E3E3)
val InverseOnSurfaceDark = Color(0xFF2E3132)
val InversePrimaryDark = Color(0xFF006874)

// ═══════════════════════════════════════════════════════════════
// Clinical State Palette — Risk Communication Colors
// These are independent of Material 3 roles and NEVER used
// decoratively. Each always paired with icon + text label.
// ═══════════════════════════════════════════════════════════════
val StateGreen = Color(0xFF1B6E2C)           // Low / Safe
val StateGreenContainer = Color(0xFFB7F1B9)
val StateAmber = Color(0xFFB45309)           // Medium / Monitor
val StateAmberContainer = Color(0xFFFFF3E0)
val StateDeepOrange = Color(0xFFC2410C)      // High / Refer
val StateDeepOrangeContainer = Color(0xFFFFE0D0)
val StateCrimson = Color(0xFF9B1C1C)         // Critical / Emergency
val StateCrimsonContainer = Color(0xFFFFDAD6)

// On-state colors (white text on all risk badges)
val OnStateColor = Color(0xFFFFFFFF)

// Accent for teal-tinted cards
val TealTint = Color(0xFFE0F7FA)
