package com.ayushbot.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.ayushbot.app.ui.theme.StateAmber
import com.ayushbot.app.ui.theme.StateCrimson
import com.ayushbot.app.ui.theme.StateGreen

@Composable
fun SignalQualityIndicator(
    quality: Float,
    modifier: Modifier = Modifier,
) {
    val clamped = quality.coerceIn(0f, 1f)
    val activeBars = when {
        clamped >= 0.8f -> 3
        clamped >= 0.5f -> 2
        clamped > 0f -> 1
        else -> 0
    }

    val color = when {
        clamped >= 0.8f -> StateGreen
        clamped >= 0.5f -> StateAmber
        else -> StateCrimson
    }

    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        repeat(3) { index ->
            val barColor = if (index < activeBars) color else MaterialTheme.colorScheme.surfaceVariant
            val barHeight = (index + 1) * 4
            Row(
                modifier = Modifier
                    .width(6.dp)
                    .height(barHeight.dp)
                    .background(barColor)
            ) {}
        }
    }
}
