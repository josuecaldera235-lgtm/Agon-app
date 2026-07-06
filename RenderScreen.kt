package com.agon.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.agon.app.viewmodel.CreateViewModel

@Composable
fun RenderScreen(
    viewModel: CreateViewModel,
    onDone: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val cs = MaterialTheme.colorScheme
    val progress = state.renderProgress
    val isDone = progress >= 100

    val animatedProgress by animateFloatAsState(
        targetValue = progress / 100f,
        animationSpec = tween(400, easing = LinearEasing),
        label = "progress",
    )

    // rotating shimmer ring
    val infinite = rememberInfiniteTransition(label = "ring")
    val rotation by infinite.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(1400, easing = LinearEasing), RepeatMode.Restart),
        label = "rot",
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(listOf(cs.background, cs.surface))
            ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            // Status ring
            Box(contentAlignment = Alignment.Center) {
                if (!isDone) {
                    Box(
                        Modifier
                            .size(140.dp)
                            .clip(RoundedCornerShape(50))
                            .background(
                                Brush.sweepGradient(
                                    listOf(cs.primary, cs.tertiary, cs.secondary, cs.primary)
                                )
                            )
                            .rotate(rotation)
                    )
                    Box(
                        Modifier.size(116.dp).clip(RoundedCornerShape(50)).background(cs.background),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            "$progress%",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            color = cs.primary,
                        )
                    }
                } else {
                    Box(
                        Modifier.size(120.dp).clip(RoundedCornerShape(50))
                            .background(Brush.linearGradient(listOf(cs.primary, cs.secondary))),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            Icons.Default.CheckCircle, contentDescription = null,
                            tint = Color.White, modifier = Modifier.size(60.dp),
                        )
                    }
                }
            }

            Spacer(Modifier.height(32.dp))
            Text(
                if (isDone) "Video ready!" else "Rendering your video",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = cs.onBackground,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                if (isDone) "Your clip has been added to your library"
                else state.renderStage.ifBlank { "Initialising…" },
                style = MaterialTheme.typography.bodyMedium,
                color = cs.onSurfaceVariant,
            )

            Spacer(Modifier.height(28.dp))
            LinearProgressIndicator(
                progress = { animatedProgress },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(50)),
                color = cs.primary,
                trackColor = cs.surfaceVariant,
            )

            Spacer(Modifier.height(36.dp))
            AnimatedVisibility(visible = isDone, enter = fadeIn(), exit = fadeOut()) {
                Button(
                    onClick = onDone,
                    modifier = Modifier.fillMaxWidth().height(54.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = cs.primary, contentColor = cs.onPrimary,
                    ),
                ) {
                    Text("View in library", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}
