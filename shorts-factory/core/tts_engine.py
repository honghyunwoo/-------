"""
TTS 엔진 모듈
텍스트를 음성으로 변환 (TYPECAST, ElevenLabs)
"""

import os
import time
import requests
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


class TTSProvider(Enum):
    """TTS 제공자"""
    TYPECAST = "typecast"
    ELEVENLABS = "elevenlabs"
    EDGE = "edge"  # 무료 Edge TTS


@dataclass
class TTSConfig:
    """TTS 설정"""
    provider: TTSProvider
    voice_id: str
    speed: float = 1.0
    pitch: float = 0.0
    sample_rate: int = 22050


class BaseTTSEngine(ABC):
    """TTS 엔진 베이스 클래스"""

    @abstractmethod
    def generate(self, text: str, output_path: Path) -> Path:
        """텍스트를 음성으로 변환"""
        pass

    @abstractmethod
    def get_voices(self) -> list:
        """사용 가능한 음성 목록"""
        pass


class TypecastEngine(BaseTTSEngine):
    """TYPECAST TTS 엔진 (한국어)"""

    API_BASE = "https://typecast.ai/api"

    # 기본 한국어 음성 ID (추후 실제 ID로 교체)
    DEFAULT_VOICES = {
        "male_warm": "5f7b9b9b9b9b9b9b9b9b9b9b",  # 따뜻한 남성
        "female_calm": "5f7b9b9b9b9b9b9b9b9b9b9c",  # 차분한 여성
        "male_deep": "5f7b9b9b9b9b9b9b9b9b9b9d",  # 깊은 남성
    }

    def __init__(self, api_key: str, voice_id: str = None):
        self.api_key = api_key
        self.voice_id = voice_id or self.DEFAULT_VOICES.get("male_warm")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, text: str, output_path: Path) -> Path:
        """TYPECAST API로 TTS 생성"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 음성 생성 요청
        speak_url = f"{self.API_BASE}/speak"
        payload = {
            "actor_id": self.voice_id,
            "text": text,
            "lang": "ko",
            "tempo": 1.0,
            "volume": 100,
            "pitch": 0,
        }

        try:
            response = requests.post(
                speak_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # 2. 음성 생성 대기 및 다운로드
            speak_url = result.get("result", {}).get("speak_v2_url")
            if speak_url:
                audio_response = self._wait_and_download(speak_url)
                with open(output_path, "wb") as f:
                    f.write(audio_response)
                return output_path
            else:
                raise TTSError("TYPECAST: 음성 URL을 받지 못했습니다")

        except requests.RequestException as e:
            raise TTSError(f"TYPECAST API 오류: {e}")

    def _wait_and_download(self, speak_url: str, max_retries: int = 30) -> bytes:
        """음성 생성 완료 대기 후 다운로드"""
        for _ in range(max_retries):
            response = requests.get(speak_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                status = result.get("result", {}).get("status")

                if status == "done":
                    audio_url = result.get("result", {}).get("audio_download_url")
                    if audio_url:
                        audio_response = requests.get(audio_url, timeout=60)
                        return audio_response.content
                elif status == "failed":
                    raise TTSError("TYPECAST: 음성 생성 실패")

            time.sleep(1)

        raise TTSError("TYPECAST: 음성 생성 타임아웃")

    def get_voices(self) -> list:
        """사용 가능한 음성 목록"""
        try:
            response = requests.get(
                f"{self.API_BASE}/actors",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except requests.RequestException:
            return list(self.DEFAULT_VOICES.keys())


class ElevenLabsEngine(BaseTTSEngine):
    """ElevenLabs TTS 엔진 (영어)"""

    API_BASE = "https://api.elevenlabs.io/v1"

    # 기본 영어 음성 ID
    DEFAULT_VOICES = {
        "adam": "pNInz6obpgDQGcFmaJgB",  # Adam - 깊고 내레이션 적합
        "josh": "TxGEqnHWrfWFTfGW9XjX",  # Josh - 젊고 역동적
        "rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel - 차분한 여성
        "domi": "AZnzlk1XvdvUeBnXmlld",  # Domi - 강렬한 여성
    }

    def __init__(self, api_key: str, voice_id: str = None):
        self.api_key = api_key
        self.voice_id = voice_id or self.DEFAULT_VOICES.get("adam")
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

    def generate(self, text: str, output_path: Path) -> Path:
        """ElevenLabs API로 TTS 생성"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"{self.API_BASE}/text-to-speech/{self.voice_id}"

        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

        except requests.RequestException as e:
            raise TTSError(f"ElevenLabs API 오류: {e}")

    def get_voices(self) -> list:
        """사용 가능한 음성 목록"""
        try:
            response = requests.get(
                f"{self.API_BASE}/voices",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            voices = response.json().get("voices", [])
            return [{"id": v["voice_id"], "name": v["name"]} for v in voices]
        except requests.RequestException:
            return [{"id": v, "name": k} for k, v in self.DEFAULT_VOICES.items()]


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS 엔진 (무료, 한국어/영어 모두 지원)"""

    # 한국어 음성 목록
    KOREAN_VOICES = {
        "sunhi": "ko-KR-SunHiNeural",  # 여성, 밝고 친근
        "injoon": "ko-KR-InJoonNeural",  # 남성, 차분하고 신뢰감
        "hyunsu": "ko-KR-HyunsuNeural",  # 남성, 따뜻한 목소리
        "bongJin": "ko-KR-BongJinNeural",  # 남성
        "gookMin": "ko-KR-GookMinNeural",  # 남성
        "jiMin": "ko-KR-JiMinNeural",  # 여성
        "seoHyeon": "ko-KR-SeoHyeonNeural",  # 여성
        "soonBok": "ko-KR-SoonBokNeural",  # 여성
        "yuJin": "ko-KR-YuJinNeural",  # 여성
    }

    # 영어 음성 목록
    ENGLISH_VOICES = {
        "guy": "en-US-GuyNeural",  # 남성
        "jenny": "en-US-JennyNeural",  # 여성
        "aria": "en-US-AriaNeural",  # 여성
        "davis": "en-US-DavisNeural",  # 남성
    }

    def __init__(self, voice_id: str = None, lang: str = "ko"):
        self.lang = lang
        if lang == "ko":
            self.voice_id = voice_id or self.KOREAN_VOICES.get("injoon")
        else:
            self.voice_id = voice_id or self.ENGLISH_VOICES.get("guy")

    def generate(self, text: str, output_path: Path) -> Path:
        """Edge TTS로 음성 생성"""
        import asyncio
        import edge_tts

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async def _generate():
            communicate = edge_tts.Communicate(text, self.voice_id)
            await communicate.save(str(output_path))

        asyncio.run(_generate())
        return output_path

    def get_voices(self) -> list:
        """사용 가능한 음성 목록"""
        if self.lang == "ko":
            return [{"id": v, "name": k} for k, v in self.KOREAN_VOICES.items()]
        else:
            return [{"id": v, "name": k} for k, v in self.ENGLISH_VOICES.items()]


class TTSError(Exception):
    """TTS 관련 예외"""
    pass


class TTSEngine:
    """TTS 엔진 팩토리 및 통합 인터페이스"""

    def __init__(
        self,
        provider: TTSProvider,
        api_key: str = None,
        voice_id: str = None,
        lang: str = "ko"
    ):
        self.provider = provider

        if provider == TTSProvider.TYPECAST:
            self.engine = TypecastEngine(api_key, voice_id)
        elif provider == TTSProvider.ELEVENLABS:
            self.engine = ElevenLabsEngine(api_key, voice_id)
        elif provider == TTSProvider.EDGE:
            self.engine = EdgeTTSEngine(voice_id, lang)
        else:
            raise ValueError(f"지원하지 않는 TTS 제공자: {provider}")

    def generate(self, text: str, output_path: Path) -> Path:
        """텍스트를 음성으로 변환"""
        return self.engine.generate(text, output_path)

    def get_voices(self) -> list:
        """사용 가능한 음성 목록"""
        return self.engine.get_voices()

    @classmethod
    def from_config(cls, config: TTSConfig, api_key: str) -> 'TTSEngine':
        """설정에서 엔진 생성"""
        return cls(
            provider=config.provider,
            api_key=api_key,
            voice_id=config.voice_id
        )


def get_audio_duration(audio_path: Path) -> float:
    """오디오 파일 길이 반환 (초)"""
    try:
        # MoviePy 사용 (Python 3.13 호환)
        from moviepy import AudioFileClip
        with AudioFileClip(str(audio_path)) as audio:
            return audio.duration
    except Exception:
        try:
            # mutagen 백업
            from mutagen.mp3 import MP3
            audio = MP3(str(audio_path))
            return audio.info.length
        except Exception as e:
            raise TTSError(f"오디오 길이 측정 실패: {e}")
