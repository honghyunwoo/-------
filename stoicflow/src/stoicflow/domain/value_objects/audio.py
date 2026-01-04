"""Audio-related value objects."""

from pathlib import Path

from pydantic import BaseModel, Field


class VoiceConfig(BaseModel):
    """Voice configuration for TTS."""

    voice_id: str = Field(description="Voice identifier (provider-specific)")
    language: str = Field(default="ko-KR", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=1.0, ge=0.5, le=1.5, description="Voice pitch")


class AudioClip(BaseModel):
    """An audio clip with timing information."""

    path: Path = Field(description="Path to audio file")
    duration: float = Field(description="Duration in seconds")
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    channels: int = Field(default=2, description="Number of audio channels")
    format: str = Field(default="wav", description="Audio format")

    # Timing in video
    start_time: float = Field(default=0.0, description="Start time in video")
    end_time: float | None = Field(default=None, description="End time in video")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Volume multiplier")

    @property
    def end(self) -> float:
        """Get end time (calculated if not set)."""
        return self.end_time if self.end_time is not None else self.start_time + self.duration
