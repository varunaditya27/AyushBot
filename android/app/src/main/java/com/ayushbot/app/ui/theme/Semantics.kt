package com.ayushbot.app.ui.theme

import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics

fun Modifier.ayushHeading(): Modifier = semantics { heading() }

fun Modifier.ayushLiveRegionCritical(isCritical: Boolean): Modifier = semantics {
    liveRegion = if (isCritical) LiveRegionMode.Assertive else LiveRegionMode.Polite
}

fun Modifier.ayushDecorative(): Modifier = clearAndSetSemantics { }
