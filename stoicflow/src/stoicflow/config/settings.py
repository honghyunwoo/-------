"""
StoicFlow Configuration using Pydantic Settings

Supports .env file and environment variables
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="STOICFLOW_",
    )

    # LLM Settings
    llm_provider: Literal["claude", "gemini", "ollama"] = Field(
        default="claude",
        description="LLM provider for script generation",
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key for Claude",
    )
    gemini_api_key: SecretStr | None = Field(
        default=None,
        description="Google Gemini API key",
    )
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server host for local LLM",
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model name",
    )

    # TTS Settings
    tts_provider: Literal["edge", "elevenlabs", "skip"] = Field(
        default="skip",  # Default to skip (user records voice)
        description="TTS provider - 'skip' for manual recording workflow",
    )
    elevenlabs_api_key: SecretStr | None = Field(
        default=None,
        description="ElevenLabs API key for premium TTS",
    )
    edge_voice: str = Field(
        default="ko-KR-SunHiNeural",
        description="Microsoft Edge TTS voice ID",
    )

    # Video Settings
    video_width: int = Field(default=1080, description="Video width in pixels")
    video_height: int = Field(default=1920, description="Video height in pixels (9:16)")
    video_fps: int = Field(default=30, description="Video frames per second")
    background_music_volume: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Background music volume (0-1)",
    )

    # Subtitle Settings
    subtitle_font: str = Field(
        default="NanumGothic",
        description="Subtitle font family",
    )
    subtitle_font_size: int = Field(default=60, description="Subtitle font size")
    subtitle_color: str = Field(default="white", description="Subtitle text color")
    subtitle_stroke_color: str = Field(default="black", description="Subtitle stroke color")
    subtitle_stroke_width: int = Field(default=3, description="Subtitle stroke width")

    # YouTube Settings
    youtube_client_secrets: str = Field(
        default="client_secret.json",
        description="Path to YouTube OAuth client secrets file",
    )
    youtube_default_privacy: Literal["public", "private", "unlisted"] = Field(
        default="private",
        description="Default privacy status for uploads",
    )
    youtube_default_category: str = Field(
        default="22",  # People & Blogs
        description="Default YouTube category ID",
    )

    # Media Settings
    pexels_api_key: SecretStr | None = Field(
        default=None,
        description="Pexels API key for stock videos",
    )

    # Path Settings
    data_dir: Path = Field(
        default=Path("data"),
        description="Base data directory",
    )

    @property
    def scripts_dir(self) -> Path:
        """Directory for script files."""
        return self.data_dir / "scripts"

    @property
    def media_dir(self) -> Path:
        """Directory for media assets."""
        return self.data_dir / "media"

    @property
    def output_dir(self) -> Path:
        """Directory for generated videos."""
        return self.data_dir / "output"

    @property
    def tokens_dir(self) -> Path:
        """Directory for OAuth tokens."""
        return self.data_dir / "tokens"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for directory in [
            self.scripts_dir,
            self.media_dir,
            self.media_dir / "backgrounds",
            self.media_dir / "music",
            self.media_dir / "fonts",
            self.output_dir,
            self.tokens_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
