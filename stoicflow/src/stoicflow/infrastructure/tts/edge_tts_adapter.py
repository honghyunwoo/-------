"""Microsoft Edge TTS adapter - Free Korean TTS."""

import asyncio
from pathlib import Path

import edge_tts
from loguru import logger

from stoicflow.application.interfaces.tts_provider import TTSProvider
from stoicflow.config.settings import settings
from stoicflow.domain.entities.script import Script
from stoicflow.domain.value_objects.audio import AudioClip, VoiceConfig

# Korean voices available in Edge TTS
KOREAN_VOICES = {
    "ko-KR-SunHiNeural": "여성 (Sun-Hi) - 밝고 친근한 목소리",
    "ko-KR-InJoonNeural": "남성 (In-Joon) - 차분하고 신뢰감 있는 목소리",
    "ko-KR-BongJinNeural": "남성 (Bong-Jin) - 뉴스 앵커 스타일",
    "ko-KR-GookMinNeural": "남성 (Gook-Min) - 젊고 활기찬 목소리",
    "ko-KR-JiMinNeural": "여성 (Ji-Min) - 부드럽고 따뜻한 목소리",
    "ko-KR-SeoHyeonNeural": "여성 (Seo-Hyeon) - 전문적이고 명확한 목소리",
    "ko-KR-SoonBokNeural": "여성 (Soon-Bok) - 성숙하고 안정된 목소리",
    "ko-KR-YuJinNeural": "여성 (Yu-Jin) - 젊고 생동감 있는 목소리",
}


class EdgeTTSAdapter(TTSProvider):
    """
    Microsoft Edge TTS를 사용하는 무료 TTS 어댑터.

    장점:
    - 완전 무료
    - 높은 품질의 한국어 음성
    - 다양한 음성 선택 가능
    - 속도/피치 조절 가능
    """

    def __init__(self, voice: str | None = None):
        self.default_voice = voice or settings.edge_voice

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        """텍스트를 음성으로 변환."""
        voice = voice_config.voice_id if voice_config else self.default_voice

        logger.debug(f"Synthesizing with EdgeTTS: {voice}")

        # Create communicate instance
        communicate = edge_tts.Communicate(text, voice)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await communicate.save(str(output_path))

        # Get duration
        duration = await self._get_audio_duration(output_path)

        logger.info(f"EdgeTTS synthesized: {output_path} ({duration:.1f}s)")

        return AudioClip(
            path=output_path,
            duration=duration,
            format="mp3",
        )

    async def synthesize_script(
        self,
        script: Script,
        output_path: Path,
        voice_config: VoiceConfig | None = None,
    ) -> AudioClip:
        """스크립트 전체를 음성으로 변환."""
        # Use tts_text if available, otherwise use full_text
        text = script.tts_text if script.tts_text else script.full_text
        return await self.synthesize(text, output_path, voice_config)

    async def list_voices(self, language: str = "ko-KR") -> list[VoiceConfig]:
        """사용 가능한 음성 목록 반환."""
        voices = await edge_tts.list_voices()

        return [
            VoiceConfig(
                voice_id=voice["ShortName"],
                language=voice["Locale"],
            )
            for voice in voices
            if voice["Locale"].startswith(language.split("-")[0])
        ]

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """오디오 파일의 길이를 반환."""
        try:
            from moviepy import AudioFileClip

            with AudioFileClip(str(audio_path)) as audio:
                return audio.duration
        except Exception:
            # Fallback: estimate from file size
            import os

            size = os.path.getsize(audio_path)
            # Rough estimate: MP3 at 128kbps ~ 16KB/s
            return size / 16000

    @classmethod
    def get_recommended_voice(cls, style: str = "calm") -> str:
        """
        스타일에 맞는 추천 음성 반환.

        Args:
            style: calm, energetic, professional, warm

        Returns:
            Voice ID
        """
        recommendations = {
            "calm": "ko-KR-InJoonNeural",  # 차분한 남성
            "energetic": "ko-KR-YuJinNeural",  # 활기찬 여성
            "professional": "ko-KR-SeoHyeonNeural",  # 전문적인 여성
            "warm": "ko-KR-SunHiNeural",  # 따뜻한 여성
        }
        return recommendations.get(style, "ko-KR-SunHiNeural")
