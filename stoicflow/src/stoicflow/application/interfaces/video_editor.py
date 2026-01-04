"""Video Editor interface (port)."""

from abc import ABC, abstractmethod
from pathlib import Path

from stoicflow.domain.entities.video import Video, VideoSpec
from stoicflow.domain.value_objects.audio import AudioClip
from stoicflow.domain.value_objects.subtitle import Subtitle


class VideoEditor(ABC):
    """
    Abstract interface for video editing operations.

    Implementations: MoviePyAdapter, FFmpegAdapter
    """

    @abstractmethod
    async def compose(
        self,
        output_path: Path,
        spec: VideoSpec,
        background: Path | None = None,
        audio: AudioClip | None = None,
        subtitles: list[Subtitle] | None = None,
        background_music: Path | None = None,
        background_music_volume: float = 0.1,
    ) -> Video:
        """
        Compose a complete video from components.

        Args:
            output_path: Where to save the video
            spec: Video specifications (resolution, fps, etc.)
            background: Background video or image path
            audio: Main audio (voice) clip
            subtitles: List of subtitles to overlay
            background_music: Optional background music path
            background_music_volume: Volume for background music

        Returns:
            Composed Video entity
        """
        ...

    @abstractmethod
    async def add_subtitles(
        self,
        video_path: Path,
        subtitles: list[Subtitle],
        output_path: Path,
    ) -> Path:
        """Add subtitles to an existing video."""
        ...

    @abstractmethod
    async def get_duration(self, media_path: Path) -> float:
        """Get duration of a video or audio file."""
        ...

    @abstractmethod
    async def extract_audio(self, video_path: Path, output_path: Path) -> AudioClip:
        """Extract audio from a video file."""
        ...

    @abstractmethod
    async def create_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float = 0.0,
    ) -> Path:
        """Create a thumbnail from a video frame."""
        ...
