package com.agon.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.MovieFilter
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.outlined.MovieFilter
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.agon.app.data.Durations
import com.agon.app.data.Engines
import com.agon.app.data.Formats
import com.agon.app.data.Styles
import com.agon.app.ui.components.CheckDot
import com.agon.app.ui.components.GradientBox
import com.agon.app.ui.components.SectionHeader
import com.agon.app.ui.components.SelectableChip
import com.agon.app.viewmodel.CreateViewModel

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun CreateScreen(
    viewModel: CreateViewModel,
    onGenerate: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val cfg = state.config
    val scroll = rememberScrollState()
    val canGenerate = cfg.prompt.isNotBlank() && !state.isGenerating

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .verticalScroll(scroll),
    ) {
        // Hero header
        HeroHeader()

        Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(28.dp)) {
            // Prompt
            SectionHeader("Describe your video", "Write a detailed prompt for the best results")
            OutlinedTextField(
                value = cfg.prompt,
                onValueChange = viewModel::updatePrompt,
                modifier = Modifier.fillMaxWidth(),
                placeholder = {
                    Text(
                        "e.g. A cinematic drone shot flying over a neon-lit Tokyo street at night, rain reflecting holographic billboards…",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                },
                minLines = 4,
                shape = RoundedCornerShape(18.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant,
                    cursorColor = MaterialTheme.colorScheme.primary,
                ),
            )

            // AI Engine
            SectionHeader("AI engine", "Choose the model that powers your video")
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(Engines.ALL) { engine ->
                    EngineCard(
                        name = engine.name,
                        tagline = engine.tagline,
                        badge = engine.badge,
                        speed = engine.speed,
                        maxRes = engine.maxResolution,
                        selected = cfg.engine.id == engine.id,
                        onClick = { viewModel.updateEngine(engine) },
                    )
                }
            }

            // Visual style
            SectionHeader("Visual style", "Define the look and feel")
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Styles.ALL.forEach { style ->
                    SelectableChip(
                        label = style.name,
                        selected = cfg.styleId == style.id,
                        onClick = { viewModel.updateStyle(style.id) },
                    )
                }
            }

            // Duration
            SectionHeader("Duration", "Length of the generated clip")
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Durations.OPTIONS.forEach { d ->
                    SelectableChip(
                        label = "${d}s",
                        selected = cfg.durationSec == d,
                        onClick = { viewModel.updateDuration(d) },
                    )
                }
            }

            // Format
            SectionHeader("Format", "Aspect ratio for your destination")
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Formats.ALL.forEach { f ->
                    FormatCard(
                        label = f.label,
                        ratio = f.ratio,
                        selected = cfg.aspectLabel == f.label,
                        onClick = { viewModel.updateAspect(f.label) },
                        modifier = Modifier.weight(1f),
                    )
                }
            }

            Spacer(Modifier.height(4.dp))

            // Generate button
            Button(
                onClick = onGenerate,
                enabled = canGenerate,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(58.dp),
                shape = RoundedCornerShape(18.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                    disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                    disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
                ),
            ) {
                Icon(Icons.Outlined.AutoAwesome, contentDescription = null, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    if (state.isGenerating) "Generating…" else "Generate video",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun HeroHeader() {
    val cs = MaterialTheme.colorScheme
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(20.dp)
            .height(150.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(cs.primary, cs.tertiary, cs.secondary),
                )
            ),
    ) {
        Column(
            modifier = Modifier.padding(22.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.MovieFilter, contentDescription = null, tint = Color.White, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(8.dp))
                Text("Create", color = Color.White, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
            }
            Column {
                Text(
                    "Idea to video",
                    style = MaterialTheme.typography.headlineMedium,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    "in seconds",
                    style = MaterialTheme.typography.headlineMedium,
                    color = Color.White.copy(alpha = 0.85f),
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

@Composable
private fun EngineCard(
    name: String,
    tagline: String,
    badge: String,
    speed: String,
    maxRes: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val cs = MaterialTheme.colorScheme
    Surface(
        modifier = Modifier
            .width(180.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        color = if (selected) cs.primaryContainer else cs.surfaceVariant,
        border = androidx.compose.foundation.BorderStroke(
            if (selected) 2.dp else 0.dp,
            if (selected) cs.primary else Color.Transparent,
        ),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    Modifier.size(40.dp).clip(RoundedCornerShape(12.dp))
                        .background(if (selected) cs.primary else cs.surfaceContainer),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.Default.MovieFilter, contentDescription = null,
                        tint = if (selected) cs.onPrimary else cs.onSurfaceVariant, modifier = Modifier.size(22.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(name, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold,
                        color = if (selected) cs.onPrimaryContainer else cs.onSurface)
                    if (badge.isNotBlank()) {
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = cs.tertiary,
                        ) {
                            Text(badge, style = MaterialTheme.typography.labelSmall, color = cs.onTertiary,
                                fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp))
                        }
                    }
                }
                CheckDot(selected)
            }
            Spacer(Modifier.height(12.dp))
            Text(tagline, style = MaterialTheme.typography.bodySmall,
                color = if (selected) cs.onPrimaryContainer else cs.onSurfaceVariant, maxLines = 2)
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                EngineMeta(Icons.Default.Bolt, speed)
                EngineMeta(Icons.Default.PlayArrow, maxRes)
            }
        }
    }
}

@Composable
private fun EngineMeta(icon: androidx.compose.ui.graphics.vector.ImageVector, text: String) {
    val cs = MaterialTheme.colorScheme
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, contentDescription = null, tint = cs.onSurfaceVariant, modifier = Modifier.size(14.dp))
        Spacer(Modifier.width(3.dp))
        Text(text, style = MaterialTheme.typography.labelSmall, color = cs.onSurfaceVariant)
    }
}

@Composable
private fun FormatCard(
    label: String,
    ratio: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val cs = MaterialTheme.colorScheme
    Surface(
        modifier = modifier.clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        color = if (selected) cs.primaryContainer else cs.surfaceVariant,
        border = androidx.compose.foundation.BorderStroke(
            if (selected) 2.dp else 0.dp,
            if (selected) cs.primary else Color.Transparent,
        ),
    ) {
        Column(
            Modifier.padding(vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Box(
                Modifier
                    .padding(bottom = 10.dp)
                    .clip(RoundedCornerShape(4.dp))
                    .background(if (selected) cs.primary else cs.onSurfaceVariant.copy(alpha = 0.4f))
                    .then(
                        when (ratio) {
                            "16:9" -> Modifier.size(width = 44.dp, height = 26.dp)
                            "9:16" -> Modifier.size(width = 26.dp, height = 44.dp)
                            else -> Modifier.size(34.dp)
                        }
                    ),
            )
            Text(label, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold,
                color = if (selected) cs.onPrimaryContainer else cs.onSurface)
            Text(ratio, style = MaterialTheme.typography.labelSmall,
                color = if (selected) cs.onPrimaryContainer else cs.onSurfaceVariant)
        }
    }
}
