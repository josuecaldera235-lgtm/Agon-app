package com.agon.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.agon.app.data.AiEngine
import com.agon.app.data.Engines
import com.agon.app.data.RenderStatus
import com.agon.app.data.Styles
import com.agon.app.data.VideoProject
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

data class CreateConfig(
    val prompt: String = "",
    val engine: AiEngine = Engines.ALL[0],
    val styleId: String = Styles.ALL[0].id,
    val durationSec: Int = 10,
    val aspectLabel: String = "16:9",
)

data class CreateUiState(
    val config: CreateConfig = CreateConfig(),
    val isGenerating: Boolean = false,
    val renderProgress: Int = 0,
    val renderStage: String = "",
)

class CreateViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(CreateUiState())
    val uiState: StateFlow<CreateUiState> = _uiState.asStateFlow()

    private val _projects = MutableStateFlow(seedProjects())
    val projects: StateFlow<List<VideoProject>> = _projects.asStateFlow()

    fun updatePrompt(v: String) = _uiState.update { it.copy(config = it.config.copy(prompt = v)) }
    fun updateEngine(e: AiEngine) = _uiState.update { it.copy(config = it.config.copy(engine = e)) }
    fun updateStyle(id: String) = _uiState.update { it.copy(config = it.config.copy(styleId = id)) }
    fun updateDuration(d: Int) = _uiState.update { it.copy(config = it.config.copy(durationSec = d)) }
    fun updateAspect(label: String) = _uiState.update { it.copy(config = it.config.copy(aspectLabel = label)) }

    private val renderStages = listOf(
        "Parsing prompt…",
        "Generating keyframes…",
        "Synthesising motion…",
        "Rendering frames…",
        "Upscaling & colour grading…",
        "Encoding output…",
    )

    fun startRender(onComplete: (VideoProject) -> Unit) {
        val cfg = _uiState.value.config
        if (cfg.prompt.isBlank()) return
        viewModelScope.launch {
            _uiState.update { it.copy(isGenerating = true, renderProgress = 0) }
            val style = Styles.ALL.first { it.id == cfg.styleId }
            val thumb = pickThumb(cfg.styleId)
            val project = VideoProject(
                id = UUID.randomUUID().toString(),
                prompt = cfg.prompt,
                engineId = cfg.engine.id,
                engineName = cfg.engine.name,
                styleId = cfg.styleId,
                styleName = style.name,
                durationSec = cfg.durationSec,
                aspectLabel = cfg.aspectLabel,
                aspectRatio = cfg.aspectLabel,
                thumbnailRes = thumb,
                status = RenderStatus.RENDERING,
                progress = 0,
            )
            _projects.update { listOf(project) + it }

            // Simulate render progress
            val total = 100
            var p = 0
            while (p < total) {
                val step = (3..9).random()
                p = (p + step).coerceAtMost(total)
                val stageIndex = ((p / 100.0) * renderStages.size).toInt().coerceIn(0, renderStages.lastIndex)
                _uiState.update { it.copy(renderProgress = p, renderStage = renderStages[stageIndex]) }
                _projects.update { list ->
                    list.map { if (it.id == project.id) it.copy(progress = p) else it }
                }
                delay(120L)
            }
            val done = project.copy(status = RenderStatus.COMPLETED, progress = 100)
            _projects.update { list -> list.map { if (it.id == project.id) done else it } }
            _uiState.update { it.copy(isGenerating = false, renderProgress = 100, renderStage = "Done") }
            onComplete(done)
        }
    }

    fun deleteProject(id: String) {
        _projects.update { list -> list.filterNot { it.id == id } }
    }

    private fun pickThumb(styleId: String): String = when (styleId) {
        "cinematic", "cyberpunk" -> "sample_cinematic"
        "realistic", "vintage" -> "sample_portrait"
        "3d", "watercolor" -> "sample_abstract"
        "anime" -> "sample_ocean"
        "noir" -> "sample_space"
        else -> "sample_aerial"
    }

    private fun seedProjects(): List<VideoProject> = listOf(
        VideoProject(
            id = "s1", prompt = "A neon-lit cyberpunk city street in the rain at night, reflections on wet pavement",
            engineId = "sora2", engineName = "Sora 2", styleId = "cyberpunk", styleName = "Cyberpunk",
            durationSec = 15, aspectLabel = "16:9", aspectRatio = "16:9",
            thumbnailRes = "sample_cinematic", status = RenderStatus.COMPLETED, progress = 100,
        ),
        VideoProject(
            id = "s2", prompt = "Aerial drone shot soaring over misty mountain peaks at golden sunrise",
            engineId = "veo3", engineName = "Veo 3", styleId = "cinematic", styleName = "Cinematic",
            durationSec = 20, aspectLabel = "16:9", aspectRatio = "16:9",
            thumbnailRes = "sample_aerial", status = RenderStatus.COMPLETED, progress = 100,
        ),
        VideoProject(
            id = "s3", prompt = "Abstract liquid metal flowing and morphing in slow motion, iridescent colours",
            engineId = "runway4", engineName = "Runway Gen-4", styleId = "3d", styleName = "3D Render",
            durationSec = 10, aspectLabel = "1:1", aspectRatio = "1:1",
            thumbnailRes = "sample_abstract", status = RenderStatus.COMPLETED, progress = 100,
        ),
        VideoProject(
            id = "s4", prompt = "Vibrant coral reef teeming with tropical fish, dappled sunlight from above",
            engineId = "kling2", engineName = "Kling 2.5", styleId = "realistic", styleName = "Realistic",
            durationSec = 15, aspectLabel = "9:16", aspectRatio = "9:16",
            thumbnailRes = "sample_ocean", status = RenderStatus.COMPLETED, progress = 100,
        ),
        VideoProject(
            id = "s5", prompt = "Slow zoom into a swirling galaxy, stars and nebula clouds drifting",
            engineId = "luma2", engineName = "Luma Dream Machine", styleId = "cinematic", styleName = "Cinematic",
            durationSec = 20, aspectLabel = "16:9", aspectRatio = "16:9",
            thumbnailRes = "sample_space", status = RenderStatus.COMPLETED, progress = 100,
        ),
        VideoProject(
            id = "s6", prompt = "Dramatic studio portrait, red and blue rim lighting, intense gaze",
            engineId = "pika2", engineName = "Pika 2.2", styleId = "noir", styleName = "Noir",
            durationSec = 10, aspectLabel = "9:16", aspectRatio = "9:16",
            thumbnailRes = "sample_portrait", status = RenderStatus.COMPLETED, progress = 100,
        ),
    )
}
