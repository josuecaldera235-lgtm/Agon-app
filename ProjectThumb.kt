package com.agon.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.agon.app.data.RenderStatus
import com.agon.app.data.VideoProject

@Composable
fun ProjectThumb(
    project: VideoProject,
    modifier: Modifier = Modifier,
) {
    val ctx = LocalContext.current
    val resId = ctx.resources.getIdentifier(project.thumbnailRes, "drawable", ctx.packageName)
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant),
    ) {
        if (resId != 0) {
            AsyncImage(
                model = resId,
                contentDescription = project.prompt,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            Box(
                Modifier.fillMaxSize().background(MaterialTheme.colorScheme.surfaceVariant),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    Icons.Default.Movie, contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(32.dp),
                )
            }
        }
        Box(
            Modifier.fillMaxSize().background(
                Brush.verticalGradient(0.45f to Color.Transparent, 1f to Color.Black.copy(alpha = 0.75f))
            )
        )
        StatusBadge(project.status, Modifier.padding(10.dp).align(Alignment.TopStart))
        Text(
            text = "${project.durationSec}s",
            style = MaterialTheme.typography.labelSmall,
            color = Color.White,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier
                .padding(10.dp)
                .align(Alignment.TopEnd)
                .clip(RoundedCornerShape(6.dp))
                .background(Color.Black.copy(alpha = 0.55f))
                .padding(horizontal = 8.dp, vertical = 3.dp),
        )
        if (project.status == RenderStatus.COMPLETED) {
            Box(
                Modifier.align(Alignment.Center).size(48.dp).clip(RoundedCornerShape(50))
                    .background(Color.White.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    Icons.Default.PlayArrow, contentDescription = "Play", tint = Color.White,
                    modifier = Modifier.size(28.dp),
                )
            }
        }
        Column(
            Modifier.align(Alignment.BottomStart).padding(12.dp).fillMaxWidth(),
        ) {
            Text(
                text = project.prompt,
                style = MaterialTheme.typography.bodySmall,
                color = Color.White,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                fontWeight = FontWeight.Medium,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = "${project.engineName} · ${project.styleName} · ${project.aspectRatio}",
                style = MaterialTheme.typography.labelSmall,
                color = Color.White.copy(alpha = 0.75f),
            )
        }
    }
}

@Composable
private fun StatusBadge(status: RenderStatus, modifier: Modifier = Modifier) {
    val (text, color) = when (status) {
        RenderStatus.COMPLETED -> "Ready" to Color(0xFF34D399)
        RenderStatus.RENDERING -> "Rendering" to MaterialTheme.colorScheme.secondary
        RenderStatus.QUEUED -> "Queued" to Color(0xFFFBBF24)
        RenderStatus.FAILED -> "Failed" to MaterialTheme.colorScheme.error
    }
    Row(
        modifier
            .clip(RoundedCornerShape(6.dp))
            .background(color.copy(alpha = 0.92f))
            .padding(horizontal = 8.dp, vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Box(Modifier.size(6.dp).clip(RoundedCornerShape(50)).background(Color.White))
        Text(text, style = MaterialTheme.typography.labelSmall, color = Color.Black, fontWeight = FontWeight.SemiBold)
    }
}
