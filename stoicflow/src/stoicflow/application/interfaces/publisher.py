"""Publisher interface (port) for video publishing."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from pydantic import BaseModel

from stoicflow.domain.entities.video import Video


class UploadProgress(BaseModel):
    """Upload progress information."""

    percentage: float
    bytes_uploaded: int
    total_bytes: int


class PublishResult(BaseModel):
    """Result of a publish operation."""

    success: bool
    video_id: str | None = None
    video_url: str | None = None
    error: str | None = None


class Publisher(ABC):
    """
    Abstract interface for video publishing.

    Implementations: YouTubeAPIAdapter
    """

    @abstractmethod
    async def authenticate(self, user_id: str = "default") -> bool:
        """
        Authenticate with the publishing platform.

        Args:
            user_id: User identifier for credential storage

        Returns:
            True if authentication successful
        """
        ...

    @abstractmethod
    async def publish(
        self,
        video: Video,
        privacy: str = "private",
    ) -> PublishResult:
        """
        Publish a video to the platform.

        Args:
            video: Video entity with all metadata
            privacy: Privacy setting (public, private, unlisted)

        Returns:
            PublishResult with video ID and URL if successful
        """
        ...

    @abstractmethod
    async def publish_with_progress(
        self,
        video: Video,
        privacy: str = "private",
    ) -> AsyncIterator[UploadProgress | PublishResult]:
        """
        Publish a video with progress updates.

        Yields:
            UploadProgress during upload, PublishResult when complete
        """
        ...

    @abstractmethod
    async def update_metadata(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Update video metadata after publishing."""
        ...

    @abstractmethod
    async def update_thumbnail(
        self,
        video_id: str,
        thumbnail_path: str,
    ) -> bool:
        """Update video thumbnail."""
        ...
