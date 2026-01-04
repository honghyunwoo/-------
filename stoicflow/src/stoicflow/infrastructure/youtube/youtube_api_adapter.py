"""YouTube API adapter - Based on 올빼미 youtube_uploader.py."""

from pathlib import Path
from typing import AsyncIterator

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from loguru import logger

from stoicflow.application.interfaces.publisher import (
    PublishResult,
    Publisher,
    UploadProgress,
)
from stoicflow.config.settings import settings
from stoicflow.domain.entities.video import Video

# YouTube API Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeAPIAdapter(Publisher):
    """
    YouTube Data API v3를 사용하는 업로드 어댑터.

    올빼미 프로젝트의 youtube_uploader.py를 Clean Architecture에 맞게 리팩터링.
    """

    def __init__(
        self,
        client_secrets_path: Path | None = None,
        tokens_dir: Path | None = None,
    ):
        self.client_secrets_path = Path(
            client_secrets_path or settings.youtube_client_secrets
        )
        self.tokens_dir = tokens_dir or settings.tokens_dir
        self._youtube = None
        self._credentials = None

    async def authenticate(self, user_id: str = "default") -> bool:
        """YouTube API 인증."""
        token_path = self.tokens_dir / f"{user_id}_youtube_token.json"

        creds = None

        # Load existing token
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                if not self.client_secrets_path.exists():
                    logger.error(
                        f"Client secrets not found: {self.client_secrets_path}"
                    )
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secrets_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return False

            # Save token
            self.tokens_dir.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        self._credentials = creds
        self._youtube = build("youtube", "v3", credentials=creds)
        logger.success("YouTube API authenticated")
        return True

    async def publish(
        self,
        video: Video,
        privacy: str = "private",
    ) -> PublishResult:
        """비디오 업로드 (프로그레스 없이)."""
        async for result in self.publish_with_progress(video, privacy):
            if isinstance(result, PublishResult):
                return result

        return PublishResult(success=False, error="Upload failed unexpectedly")

    async def publish_with_progress(
        self,
        video: Video,
        privacy: str = "private",
    ) -> AsyncIterator[UploadProgress | PublishResult]:
        """비디오 업로드 (프로그레스 포함)."""
        if not self._youtube:
            yield PublishResult(
                success=False, error="Not authenticated. Call authenticate() first."
            )
            return

        if not video.video_path or not video.video_path.exists():
            yield PublishResult(success=False, error="Video file not found")
            return

        try:
            body = {
                "snippet": {
                    "title": video.title,
                    "description": video.description,
                    "tags": video.tags,
                    "categoryId": settings.youtube_default_category,
                },
                "status": {"privacyStatus": privacy},
            }

            # Resumable upload
            media = MediaFileUpload(
                str(video.video_path),
                chunksize=1024 * 1024,  # 1MB chunks
                resumable=True,
            )

            request = self._youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            file_size = video.video_path.stat().st_size

            while response is None:
                status, response = request.next_chunk()
                if status:
                    bytes_uploaded = int(status.resumable_progress)
                    yield UploadProgress(
                        percentage=status.progress() * 100,
                        bytes_uploaded=bytes_uploaded,
                        total_bytes=file_size,
                    )

            video_id = response.get("id")
            video_url = f"https://youtube.com/watch?v={video_id}"

            logger.success(f"Video uploaded: {video_url}")

            yield PublishResult(
                success=True,
                video_id=video_id,
                video_url=video_url,
            )

        except HttpError as e:
            logger.error(f"HTTP error during upload: {e.resp.status} - {e.content}")
            yield PublishResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            yield PublishResult(success=False, error=str(e))

    async def update_metadata(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """비디오 메타데이터 업데이트."""
        if not self._youtube:
            return False

        try:
            # Get current video info
            response = self._youtube.videos().list(
                part="snippet", id=video_id
            ).execute()

            if not response.get("items"):
                return False

            snippet = response["items"][0]["snippet"]

            # Update fields
            if title:
                snippet["title"] = title
            if description:
                snippet["description"] = description
            if tags:
                snippet["tags"] = tags

            self._youtube.videos().update(
                part="snippet",
                body={"id": video_id, "snippet": snippet},
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False

    async def update_thumbnail(
        self,
        video_id: str,
        thumbnail_path: str,
    ) -> bool:
        """비디오 썸네일 업데이트."""
        if not self._youtube:
            return False

        try:
            self._youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path),
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update thumbnail: {e}")
            return False
