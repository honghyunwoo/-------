"""TTS Provider interface (port)."""

from abc import ABC, abstractmethod
from pathlib import Path

from stoicflow.domain.entities.script import Script
from stoicflow.domain.value_objects.audio import AudioClip, VoiceConfig


class TTSProvider(ABC):
    """
    Abstract interface for Text-to-Speech providers.

    Implementations: EdgeTTSAdapter, ElevenLabsAdapter
    """

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            output_path: Where to save the audio file
            voice_config: Optional voice configuration

        Returns:
            AudioClip with path and duration
        """
        ...

    @abstractmethod
    async def synthesize_script(
        self,
        script: Script,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        """
        Synthesize entire script to speech.

        Args:
            script: Script to synthesize
            output_path: Where to save the audio file
            voice_config: Optional voice configuration

        Returns:
            AudioClip with path and duration
        """
        ...

    @abstractmethod
    async def list_voices(self, language: str = "ko-KR") -> list[VoiceConfig]:
        """List available voices for a language."""
        ...


class SkipTTSProvider(TTSProvider):
    """
    Placeholder TTS provider for manual recording workflow.

    Used when skip_tts=True (default for user recording their own voice).
    """

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        raise NotImplementedError(
            "TTS is skipped. Please record audio manually and provide the path."
        )

    async def synthesize_script(
        self,
        script: Script,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        raise NotImplementedError(
            "TTS is skipped. Use script.to_recording_guide() for recording instructions."
        )

    async def list_voices(self, language: str = "ko-KR") -> list[VoiceConfig]:
        return []
