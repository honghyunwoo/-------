"""Video entity and specifications."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    """Video processing status."""

    PENDING = "pending"
    COMPOSING = "composing"
    COMPOSED = "composed"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"


class VideoSpec(BaseModel):
    """Video specification and settings."""

    width: int = Field(default=1080, description="Video width in pixels")
    height: int = Field(default=1920, description="Video height in pixels")
    fps: int = Field(default=30, description="Frames per second")
    codec: str = Field(default="libx264", description="Video codec")
    audio_codec: str = Field(default="aac", description="Audio codec")
    bitrate: str = Field(default="8M", description="Video bitrate")

    @property
    def aspect_ratio(self) -> str:
        """Get aspect ratio string."""
        return f"{self.width}:{self.height}"

    @property
    def resolution(self) -> str:
        """Get resolution string."""
        return f"{self.width}x{self.height}"


class Video(BaseModel):
    """A video entity with metadata and paths."""

    id: str = Field(description="Unique video identifier")
    script_id: int = Field(description="Associated script ID")
    title: str = Field(description="Video title for YouTube")
    description: str = Field(default="", description="Video description")
    tags: list[str] = Field(default_factory=list, description="Video tags")

    # Paths
    video_path: Path | None = Field(default=None, description="Path to final video file")
    audio_path: Path | None = Field(default=None, description="Path to audio file")
    thumbnail_path: Path | None = Field(default=None, description="Path to thumbnail")
    background_path: Path | None = Field(default=None, description="Path to background video")

    # Specs
    spec: VideoSpec = Field(default_factory=VideoSpec)
    duration: float = Field(default=0.0, description="Video duration in seconds")

    # Status
    status: VideoStatus = Field(default=VideoStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: datetime | None = Field(default=None)

    # YouTube metadata
    youtube_id: str | None = Field(default=None, description="YouTube video ID after upload")
    youtube_url: str | None = Field(default=None, description="YouTube video URL")

    @property
    def is_ready_for_upload(self) -> bool:
        """Check if video is ready to be uploaded."""
        return (
            self.status == VideoStatus.COMPOSED
            and self.video_path is not None
            and self.video_path.exists()
        )

    def generate_youtube_description(self, hashtags: list[str] | None = None) -> str:
        """Generate formatted YouTube description."""
        parts = [self.description]

        if hashtags:
            parts.append("")
            parts.append(" ".join(f"#{tag}" for tag in hashtags))

        parts.append("")
        parts.append("---")
        parts.append("Created with StoicFlow")

        return "\n".join(parts)
