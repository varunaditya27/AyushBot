package com.ayushbot.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.theme.*

// ═══════════════════════════════════════════════════════════════
// VitalGauge — 120dp circular ring gauge for live vital signs.
// Color-thresholded: green → amber → crimson based on value.
// JetBrains Mono center display for numeric stability.
// ═══════════════════════════════════════════════════════════════

@Composable
fun VitalGauge(
    value: Float,
    maxValue: Float,
    unit: String,
    label: String,
    ringColor: Color,
    modifier: Modifier = Modifier,
    size: Dp? = null,
    signalQuality: Float = 1f, // 0..1
) {
    val dynamicSize = (LocalConfiguration.current.screenWidthDp.dp * 0.24f).coerceIn(92.dp, 132.dp)
    val gaugeSize = size ?: dynamicSize

    val animatedProgress by animateFloatAsState(
        targetValue = (value / maxValue).coerceIn(0f, 1f),
        animationSpec = tween(600, easing = FastOutSlowInEasing),
        label = "gauge_progress"
    )

    val animatedColor by animateColorAsState(
        targetValue = ringColor,
        animationSpec = tween(300),
        label = "ring_color"
    )

    val bgRingColor = MaterialTheme.colorScheme.surfaceVariant

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier,
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier.size(gaugeSize)
        ) {
            // Background ring
            Canvas(modifier = Modifier.fillMaxSize().padding(4.dp)) {
                val strokeWidth = 8.dp.toPx()
                val arcSize = Size(this.size.width - strokeWidth, this.size.height - strokeWidth)
                val topLeft = Offset(strokeWidth / 2, strokeWidth / 2)

                drawArc(
                    color = bgRingColor,
                    startAngle = -225f,
                    sweepAngle = 270f,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round),
                )

                // Progress ring
                drawArc(
                    color = animatedColor,
                    startAngle = -225f,
                    sweepAngle = 270f * animatedProgress,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round),
                )
            }

            // Center value
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = if (value > 0) value.toInt().toString() else "--",
                    style = VitalDisplayStyle,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = unit,
                    style = VitalUnitStyle,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        Spacer(Modifier.height(8.dp))

        // Label
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(4.dp))

        // Signal quality bar
        Box(
            modifier = Modifier
                .width(gaugeSize - 20.dp)
                .height(4.dp)
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                // Background
                drawRoundRect(
                    color = bgRingColor,
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(2.dp.toPx()),
                )
                // Fill
                drawRoundRect(
                    color = if (signalQuality >= 0.8f) StateGreen else StateAmber,
                    size = Size(this.size.width * signalQuality.coerceIn(0f, 1f), this.size.height),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(2.dp.toPx()),
                )
            }
        }
    }
}

/** Compute ring color based on SpO2 thresholds */
fun spo2RingColor(spo2: Float): Color = when {
    spo2 >= 95f -> StateGreen
    spo2 >= 90f -> StateAmber
    else -> StateCrimson
}

/** Compute ring color based on heart rate thresholds */
fun hrRingColor(hr: Float): Color = when {
    hr in 60f..160f -> PrimaryLight
    hr in 50f..180f -> StateAmber
    else -> StateCrimson
}

/** Compute ring color based on temperature thresholds */
fun tempRingColor(temp: Float): Color = when {
    temp in 36.0f..37.5f -> StateGreen
    temp in 35.0f..39.0f -> StateAmber
    else -> StateCrimson
}
