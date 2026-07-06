package com.agon.app.data

import kotlinx.serialization.Serializable

@Serializable
enum class RenderStatus { QUEUED, RENDERING, COMPLETED, FAILED }

@Serializable
class AspectRatio(val label: String, val ratio: String, val width: Int, val height: Int)

object Formats {
    val LANDSCAPE = AspectRatio("Landscape", "16:9", 1920, 1080)
    val PORTRAIT = AspectRatio("Portrait", "9:16", 1080, 1920)
    val SQUARE = AspectRatio("Square", "1:1", 1080, 1080)
    val ALL = listOf(LANDSCAPE, PORTRAIT, SQUARE)
}

@Serializable
data class VisualStyle(
    val id: String,
    val name: String,
    val description: String,
)

object Styles {
    val ALL = listOf(
        VisualStyle("cinematic", "Cinematic", "Film grain, shallow DOF, anamorphic"),
        VisualStyle("realistic", "Realistic", "Photoreal lighting & textures"),
        VisualStyle("anime", "Anime", "Cel-shaded, vibrant, 2D animation"),
        VisualStyle("3d", "3D Render", "Octane-style CGI, soft shadows"),
        VisualStyle("vintage", "Vintage", "Retro film, warm tones, grain"),
        VisualStyle("noir", "Noir", "High contrast B&W, dramatic"),
        VisualStyle("watercolor", "Watercolor", "Painterly, soft edges, pastel"),
        VisualStyle("cyberpunk", "Cyberpunk", "Neon, holographic, futuristic"),
    )
}

@Serializable
data class AiEngine(
    val id: String,
    val name: String,
    val tagline: String,
    val maxDurationSec: Int,
    val maxResolution: String,
    val speed: String,
    val badge: String,
)

object Engines {
    val ALL = listOf(
        AiEngine("sora2", "Sora 2", "OpenAI · flagship realism", 60, "4K", "Fast", "NEW"),
        AiEngine("veo3", "Veo 3", "Google DeepMind · audio+video", 60, "4K", "Fast", "PRO"),
        AiEngine("runway4", "Runway Gen-4", "Cinematic motion control", 30, "1080p", "Medium", ""),
        AiEngine("kling2", "Kling 2.5", "Kuaishou · hyper motion", 20, "1080p", "Fast", ""),
        AiEngine("pika2", "Pika 2.2", "Stylized & creative", 15, "1080p", "Very Fast", ""),
        AiEngine("luma2", "Luma Dream Machine", "Natural physics & fluidity", 15, "1080p", "Medium", ""),
    )
}

object Durations {
    val OPTIONS = listOf(5, 10, 15, 20, 30)
}

@Serializable
data class VideoProject(
    val id: String,
    val prompt: String,
    val engineId: String,
    val engineName: String,
    val styleId: String,
    val styleName: String,
    val durationSec: Int,
    val aspectLabel: String,
    val aspectRatio: String,
    val thumbnailRes: String,
    val status: RenderStatus,
    val progress: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
)
