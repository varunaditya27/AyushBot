package com.ayushbot.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.LocalHospital
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// RiskBadge — The single most critical UI component.
// Full-width banner, 96dp, with pulsing animation for CRITICAL.
// Color + icon + text = triple-redundant risk signaling.
// ═══════════════════════════════════════════════════════════════

enum class RiskTier(
    val label: String,
    val subtitle: String,
    val color: Color,
    val colorBright: Color,
    val icon: ImageVector,
) {
    LOW(
        label = "Low Risk: Home Management",
        subtitle = "Monitor at home, follow up in 1 week",
        color = StateGreen,
        colorBright = StateGreen,
        icon = Icons.Rounded.CheckCircle,
    ),
    MEDIUM(
        label = "Monitor: Follow-Up in 2 Days",
        subtitle = "Watch for worsening symptoms",
        color = StateAmber,
        colorBright = StateAmber,
        icon = Icons.Rounded.ErrorOutline,
    ),
    HIGH(
        label = "Refer: PHC Same Day",
        subtitle = "Patient needs medical attention today",
        color = StateDeepOrange,
        colorBright = StateDeepOrange,
        icon = Icons.Rounded.LocalHospital,
    ),
    CRITICAL(
        label = "EMERGENCY: Call 108 Now",
        subtitle = "Immediate life-threatening danger",
        color = StateCrimson,
        colorBright = Color(0xFFDC2626),
        icon = Icons.Rounded.Warning,
    ),
}

@Composable
fun RiskBadge(
    tier: RiskTier,
    modifier: Modifier = Modifier,
) {
    // Pulsing animation for CRITICAL tier (1.2 Hz)
    val infiniteTransition = rememberInfiniteTransition(label = "risk_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = if (tier == RiskTier.CRITICAL) 0.7f else 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = if (tier == RiskTier.CRITICAL) 833 else 1000,
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_alpha"
    )

    val bgColor by animateColorAsState(
        targetValue = if (tier == RiskTier.CRITICAL) {
            lerp(tier.color, tier.colorBright, 1f - pulseAlpha)
        } else {
            tier.color
        },
        label = "bg_color"
    )

    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(96.dp)
            .background(bgColor)
            .padding(horizontal = 20.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // 6dp left accent bar
        Box(
            modifier = Modifier
                .width(6.dp)
                .fillMaxHeight()
                .padding(vertical = 16.dp)
                .background(OnStateColor.copy(alpha = 0.3f))
        )

        Spacer(Modifier.width(16.dp))

        // Icon
        Icon(
            imageVector = tier.icon,
            contentDescription = tier.label,
            tint = OnStateColor,
            modifier = Modifier.size(40.dp)
        )

        Spacer(Modifier.width(16.dp))

        // Text content
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = tier.label,
                color = OnStateColor,
                fontSize = 20.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 26.sp,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = tier.subtitle,
                color = OnStateColor.copy(alpha = 0.87f),
                fontSize = 14.sp,
                fontWeight = FontWeight.Normal,
                lineHeight = 20.sp,
            )
        }
    }
}

// Helper: lerp between two colors
private fun lerp(start: Color, end: Color, fraction: Float): Color {
    return Color(
        red = start.red + (end.red - start.red) * fraction,
        green = start.green + (end.green - start.green) * fraction,
        blue = start.blue + (end.blue - start.blue) * fraction,
        alpha = start.alpha + (end.alpha - start.alpha) * fraction,
    )
}
