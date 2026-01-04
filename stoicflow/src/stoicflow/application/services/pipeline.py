"""
Main Pipeline Service - Orchestrates the entire shorts creation workflow.

This is the primary entry point for creating shorts videos.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from loguru import logger

from stoicflow.application.interfaces.llm_provider import LLMProvider
from stoicflow.application.interfaces.publisher import PublishResult, Publisher, UploadProgress
from stoicflow.application.interfaces.tts_provider import TTSProvider
from stoicflow.application.interfaces.video_editor import VideoEditor
from stoicflow.config.settings import settings
from stoicflow.domain.entities.script import Script, ScriptStatus
from stoicflow.domain.entities.video import Video, VideoSpec, VideoStatus
from stoicflow.domain.value_objects.subtitle import Subtitle


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    success: bool
    video: Video | None = None
    error: str | None = None
    stage: str = ""


class Pipeline:
    """
    Orchestrates the YouTube Shorts creation workflow.

    Workflow:
    1. Script Generation (or use existing)
    2. Audio Synthesis (or manual recording)
    3. Video Composition
    4. Thumbnail Generation
    5. SEO Optimization
    6. Publishing (optional)
    """

    def __init__(
        self,
        llm: LLMProvider,
        tts: TTSProvider,
        editor: VideoEditor,
        publisher: Publisher | None = None,
    ):
        self.llm = llm
        self.tts = tts
        self.editor = editor
        self.publisher = publisher
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        settings.ensure_directories()

    async def generate_script(
        self,
        topic: str | None = None,
        quote: str | None = None,
        author: str | None = None,
    ) -> Script:
        """
        Generate a new script using LLM.

        Args:
            topic: Topic to focus on
            quote: Specific quote to use
            author: Author of the quote

        Returns:
            Generated Script
        """
        logger.info(f"Generating script for topic: {topic or 'general stoic'}")
        script = await self.llm.generate_script(
            topic=topic,
            quote=quote,
            author=author,
        )
        logger.success(f"Script generated: {script.quote[:50]}...")
        return script

    async def synthesize_audio(
        self,
        script: Script,
        output_path: Path | None = None,
    ) -> Path:
        """
        Synthesize script to audio using TTS.

        Args:
            script: Script to synthesize
            output_path: Optional output path

        Returns:
            Path to generated audio file
        """
        if output_path is None:
            output_path = settings.output_dir / f"audio_{script.id}.wav"

        logger.info(f"Synthesizing audio for script #{script.id}")
        audio = await self.tts.synthesize_script(script, output_path)
        script.audio_path = audio.path
        script.status = ScriptStatus.RECORDED
        logger.success(f"Audio generated: {audio.path} ({audio.duration:.1f}s)")
        return audio.path

    async def compose_video(
        self,
        script: Script,
        audio_path: Path | None = None,
        background_path: Path | None = None,
        music_path: Path | None = None,
        output_path: Path | None = None,
    ) -> Video:
        """
        Compose the final video.

        Args:
            script: Script for the video
            audio_path: Path to audio file (recorded or TTS)
            background_path: Optional background video/image
            music_path: Optional background music
            output_path: Optional output path

        Returns:
            Composed Video entity
        """
        if audio_path is None:
            audio_path = script.audio_path

        if audio_path is None or not audio_path.exists():
            raise ValueError(
                f"Audio file not found. "
                f"Use synthesize_audio() or provide audio_path for script #{script.id}"
            )

        if output_path is None:
            output_path = settings.output_dir / f"shorts_{script.id}.mp4"

        logger.info(f"Composing video for script #{script.id}")

        # Get audio duration
        audio_duration = await self.editor.get_duration(audio_path)

        # Create audio clip
        from stoicflow.domain.value_objects.audio import AudioClip

        audio = AudioClip(path=audio_path, duration=audio_duration)

        # Generate subtitles from script
        subtitles = self._generate_subtitles(script, audio_duration)

        # Compose video
        spec = VideoSpec(
            width=settings.video_width,
            height=settings.video_height,
            fps=settings.video_fps,
        )

        video = await self.editor.compose(
            output_path=output_path,
            spec=spec,
            background=background_path,
            audio=audio,
            subtitles=subtitles,
            background_music=music_path,
            background_music_volume=settings.background_music_volume,
        )

        # Generate title and description
        video.title = await self.llm.generate_title(script)
        video.description = await self.llm.generate_description(script)
        video.tags = await self.llm.generate_tags(script)

        script.status = ScriptStatus.COMPOSED
        logger.success(f"Video composed: {output_path}")

        return video

    def _generate_subtitles(
        self,
        script: Script,
        total_duration: float,
    ) -> list[Subtitle]:
        """Generate subtitles from script segments."""
        subtitles = []
        segments = script.segments
        total_estimate = sum(s.duration_estimate for s in segments)
        scale = total_duration / total_estimate if total_estimate > 0 else 1.0

        current_time = 0.0
        for segment in segments:
            duration = segment.duration_estimate * scale
            subtitle = Subtitle(
                text=segment.text,
                start_time=current_time,
                end_time=current_time + duration,
            )
            # Split long subtitles into chunks
            subtitles.extend(subtitle.split_into_chunks(max_chars=30))
            current_time += duration

        return subtitles

    async def publish(
        self,
        video: Video,
        privacy: str = "private",
    ) -> PublishResult:
        """
        Publish video to YouTube.

        Args:
            video: Video to publish
            privacy: Privacy setting

        Returns:
            PublishResult with video ID and URL
        """
        if self.publisher is None:
            return PublishResult(success=False, error="Publisher not configured")

        if not video.is_ready_for_upload:
            return PublishResult(success=False, error="Video not ready for upload")

        logger.info(f"Publishing video: {video.title}")
        result = await self.publisher.publish(video, privacy=privacy)

        if result.success:
            video.youtube_id = result.video_id
            video.youtube_url = result.video_url
            video.status = VideoStatus.PUBLISHED
            logger.success(f"Published: {result.video_url}")

        return result

    async def publish_with_progress(
        self,
        video: Video,
        privacy: str = "private",
    ) -> AsyncIterator[UploadProgress | PublishResult]:
        """Publish video with progress updates."""
        if self.publisher is None:
            yield PublishResult(success=False, error="Publisher not configured")
            return

        async for update in self.publisher.publish_with_progress(video, privacy=privacy):
            yield update

    async def run(
        self,
        script: Script | None = None,
        topic: str | None = None,
        audio_path: Path | None = None,
        background_path: Path | None = None,
        music_path: Path | None = None,
        publish: bool = False,
        privacy: str = "private",
    ) -> PipelineResult:
        """
        Run the complete pipeline.

        Args:
            script: Existing script (or generate new)
            topic: Topic for script generation
            audio_path: Pre-recorded audio path
            background_path: Background video/image
            music_path: Background music
            publish: Whether to publish to YouTube
            privacy: Privacy setting if publishing

        Returns:
            PipelineResult with video and status
        """
        try:
            # Stage 1: Script
            if script is None:
                script = await self.generate_script(topic=topic)

            # Stage 2: Audio (if not provided)
            if audio_path is None and script.audio_path is None:
                try:
                    audio_path = await self.synthesize_audio(script)
                except NotImplementedError:
                    # TTS skipped - user needs to record
                    logger.warning("TTS skipped. Recording guide:")
                    print(script.to_recording_guide())
                    return PipelineResult(
                        success=False,
                        error="Audio required. Please record and provide audio_path.",
                        stage="audio",
                    )
            elif audio_path is None:
                audio_path = script.audio_path

            # Stage 3: Video Composition
            video = await self.compose_video(
                script=script,
                audio_path=audio_path,
                background_path=background_path,
                music_path=music_path,
            )

            # Stage 4: Publish (optional)
            if publish:
                result = await self.publish(video, privacy=privacy)
                if not result.success:
                    return PipelineResult(
                        success=False,
                        video=video,
                        error=result.error,
                        stage="publish",
                    )

            return PipelineResult(success=True, video=video)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return PipelineResult(success=False, error=str(e))
