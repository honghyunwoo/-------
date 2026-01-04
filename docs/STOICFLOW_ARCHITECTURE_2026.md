# StoicFlow 2026 Architecture Design

## Executive Summary

StoicFlow는 YouTube Shorts 자동화를 위한 차세대 파이프라인으로, 2026년 1월 기준 최신 Python 생태계와 업계 최고의 아키텍처 패턴을 결합합니다.

**목표**: 스토아 철학 동기부여 채널을 위한 80% 자동화된 쇼츠 제작 시스템

---

## Part 1: Technology Stack (2026년 기준)

### 1.1 Python & Package Management

| 항목 | 선택 | 이유 |
|------|------|------|
| Python | 3.13+ | JIT compiler, free-threading, 성능 15-20% 향상 |
| Package Manager | **uv** | pip 대비 10-100x 빠름, poetry/pyenv 대체 |
| Type Checking | pyright + Python 3.13 typing | TypeIs, ReadOnly, 더 정밀한 타입 체크 |

```bash
# uv로 프로젝트 초기화 (2026 표준)
uv init stoicflow
uv add pydantic moviepy[optional] anthropic
```

### 1.2 Core Dependencies

```toml
# pyproject.toml
[project]
name = "stoicflow"
version = "1.0.0"
requires-python = ">=3.13"

dependencies = [
    # Core Framework
    "pydantic>=2.5",           # 설정 & 데이터 검증
    "pydantic-settings>=2.1",  # 환경변수 관리

    # Video Processing
    "moviepy>=2.1",            # 비디오 편집 (2.x 최신)
    "imageio-ffmpeg>=0.5",     # FFmpeg 바이너리
    "pillow>=10.0",            # 이미지 처리

    # AI & TTS
    "anthropic>=0.40",         # Claude API (스크립트 생성)
    "edge-tts>=7.0",           # 무료 한국어 TTS (Microsoft)
    "elevenlabs>=1.0",         # 프리미엄 TTS (선택)
    "faster-whisper>=1.0",     # 자막 생성 (GPU 가속)

    # YouTube Integration
    "google-auth-oauthlib>=1.2",
    "google-api-python-client>=2.140",

    # UI (선택)
    "flet>=0.25",              # Flutter 기반 GUI
    "textual>=0.90",           # 터미널 TUI

    # Utilities
    "loguru>=0.7",             # 로깅
    "httpx>=0.27",             # Async HTTP
    "aiofiles>=24.1",          # Async 파일 I/O
    "rich>=13.0",              # 터미널 출력
]
```

---

## Part 2: Architecture (Clean Architecture 기반)

### 2.1 Directory Structure

```
stoicflow/
├── pyproject.toml              # uv 프로젝트 설정
├── uv.lock                     # 의존성 잠금
├── .env.example                # 환경변수 템플릿
│
├── src/
│   └── stoicflow/
│       ├── __init__.py
│       │
│       ├── domain/             # 🎯 비즈니스 엔티티
│       │   ├── entities/
│       │   │   ├── script.py       # Script, ScriptSegment
│       │   │   ├── video.py        # Video, VideoSpec
│       │   │   └── channel.py      # Channel, PublishConfig
│       │   └── value_objects/
│       │       ├── audio.py        # AudioClip, VoiceConfig
│       │       └── subtitle.py     # Subtitle, SubtitleStyle
│       │
│       ├── application/        # 🔄 Use Cases (비즈니스 로직)
│       │   ├── use_cases/
│       │   │   ├── generate_script.py
│       │   │   ├── synthesize_audio.py
│       │   │   ├── compose_video.py
│       │   │   ├── generate_thumbnail.py
│       │   │   ├── optimize_seo.py
│       │   │   └── publish_video.py
│       │   ├── interfaces/         # Port 정의
│       │   │   ├── llm_provider.py
│       │   │   ├── tts_provider.py
│       │   │   ├── video_editor.py
│       │   │   └── publisher.py
│       │   └── services/
│       │       └── pipeline.py     # 오케스트레이션
│       │
│       ├── infrastructure/     # 🔌 외부 연동 (Adapters)
│       │   ├── llm/
│       │   │   ├── claude_adapter.py
│       │   │   ├── gemini_adapter.py
│       │   │   └── ollama_adapter.py    # 오프라인 대안
│       │   ├── tts/
│       │   │   ├── edge_tts_adapter.py  # 무료 (기본값)
│       │   │   └── elevenlabs_adapter.py
│       │   ├── video/
│       │   │   ├── moviepy_adapter.py
│       │   │   └── ffmpeg_adapter.py    # 고급 연산용
│       │   ├── media/
│       │   │   ├── pexels_adapter.py    # 스톡 비디오
│       │   │   └── local_media_adapter.py
│       │   ├── youtube/
│       │   │   ├── youtube_api_adapter.py
│       │   │   └── oauth_manager.py
│       │   └── storage/
│       │       └── local_storage.py
│       │
│       ├── presentation/       # 🖥️ UI Layer
│       │   ├── cli/
│       │   │   ├── main.py         # Click/Typer CLI
│       │   │   └── commands/
│       │   ├── gui/
│       │   │   └── flet_app.py     # Flet GUI
│       │   ├── tui/
│       │   │   └── textual_app.py  # Textual TUI
│       │   └── api/
│       │       └── fastapi_app.py  # REST API (선택)
│       │
│       └── config/
│           ├── settings.py         # Pydantic Settings
│           └── providers.py        # 의존성 주입
│
├── data/
│   ├── scripts/                # 스크립트 저장
│   │   ├── stoic_premium.json
│   │   └── generated/
│   ├── media/                  # 미디어 에셋
│   │   ├── backgrounds/
│   │   ├── music/
│   │   └── fonts/
│   ├── output/                 # 생성된 비디오
│   └── tokens/                 # OAuth 토큰
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CLI    │  │   GUI    │  │   TUI    │  │   API    │        │
│  │ (Typer)  │  │  (Flet)  │  │(Textual) │  │(FastAPI) │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │                    Pipeline Service                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │  │
│  │  │ Generate │→│Synthesize│→│ Compose  │→│ Publish  │      │  │
│  │  │  Script  │ │  Audio   │ │  Video   │ │  Video   │      │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Interfaces (Ports):                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │LLMProvider │ │TTSProvider │ │VideoEditor │ │ Publisher  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ implements
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
│                                                                  │
│  LLM Adapters      TTS Adapters     Video Adapters              │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                 │
│  │ Claude   │     │ EdgeTTS  │     │ MoviePy  │                 │
│  │ Gemini   │     │ElevenLabs│     │ FFmpeg   │                 │
│  │ Ollama   │     └──────────┘     └──────────┘                 │
│  └──────────┘                                                    │
│                                                                  │
│  Media Adapters    YouTube Adapter   Storage                    │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                 │
│  │ Pexels   │     │ YouTube  │     │  Local   │                 │
│  │ Local    │     │ OAuth2   │     │  S3 (?)  │                 │
│  └──────────┘     └──────────┘     └──────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                                 │
│                                                                  │
│  Entities                      Value Objects                    │
│  ┌──────────────────────┐     ┌──────────────────────┐          │
│  │ Script               │     │ AudioClip            │          │
│  │ Video                │     │ Subtitle             │          │
│  │ Channel              │     │ VoiceConfig          │          │
│  │ PublishSchedule      │     │ VideoSpec            │          │
│  └──────────────────────┘     └──────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 3: GitHub 프로젝트 분석 결과 적용

### 3.1 참고 프로젝트 벤치마킹

| 프로젝트 | Stars | 핵심 배움 | StoicFlow 적용 |
|---------|-------|----------|---------------|
| **ShortGPT** | 12K+ | Engine 패턴 (Short/Video/Translation) | ✅ Use Case 분리 |
| **MoneyPrinter** | 12K+ | 심플한 파이프라인 UX | ✅ CLI 단순화 |
| **AI-Youtube-Shorts** | 2.7K+ | GPU 가속, Whisper 통합 | ✅ faster-whisper |
| **auto-shorts** | - | LLM 추상화 (OpenAI/Gemini/Ollama) | ✅ Provider 패턴 |
| **auto-yt-shorts** | 27 | FastAPI + Docker, Resumable Upload | ✅ API 레이어 |

### 3.2 채택한 아키텍처 패턴

```python
# 1. Provider 추상화 (auto-shorts에서 학습)
from abc import ABC, abstractmethod
from typing import Protocol

class LLMProvider(Protocol):
    """LLM 프로바이더 인터페이스"""
    async def generate_script(self, prompt: str) -> Script:
        ...

class ClaudeAdapter(LLMProvider):
    """Claude 구현체"""
    async def generate_script(self, prompt: str) -> Script:
        # Anthropic API 호출
        ...

class OllamaAdapter(LLMProvider):
    """오프라인 대안"""
    async def generate_script(self, prompt: str) -> Script:
        # 로컬 Ollama 호출
        ...
```

```python
# 2. TTS Fallback 패턴 (ShortGPT에서 학습)
class TTSService:
    def __init__(self, primary: TTSProvider, fallback: TTSProvider = None):
        self.primary = primary
        self.fallback = fallback

    async def synthesize(self, text: str) -> AudioClip:
        try:
            return await self.primary.synthesize(text)
        except Exception:
            if self.fallback:
                return await self.fallback.synthesize(text)
            raise

# 사용: ElevenLabs (프리미엄) → EdgeTTS (무료)
```

```python
# 3. Resumable Upload (auto-yt-shorts에서 학습)
class YouTubePublisher:
    async def upload(self, video_path: Path, metadata: VideoMetadata) -> str:
        media = MediaFileUpload(
            video_path,
            chunksize=1024*1024,  # 1MB chunks
            resumable=True
        )

        request = self.youtube.videos().insert(...)
        response = None

        while response is None:
            status, response = request.next_chunk()
            if status:
                yield UploadProgress(status.progress())

        return response['id']
```

---

## Part 4: 혁신적 아이디어 (Claude 제안)

### 4.1 AI-Powered Script Evolution

```python
# 스크립트 성능 학습 시스템
class ScriptEvolver:
    """
    업로드 후 성과 데이터를 수집하여
    스크립트 생성 품질을 지속적으로 개선
    """

    async def analyze_performance(self, video_id: str) -> PerformanceMetrics:
        """YouTube Analytics에서 시청 지속 시간, 좋아요 수집"""
        analytics = await self.youtube.get_analytics(video_id)
        return PerformanceMetrics(
            retention_rate=analytics.avg_view_duration / video.duration,
            engagement_rate=analytics.likes / analytics.views,
            ctr=analytics.ctr
        )

    async def evolve_prompt(self, performance: PerformanceMetrics) -> str:
        """성과 기반으로 프롬프트 개선"""
        if performance.retention_rate < 0.5:
            return "훅을 더 강렬하게, 첫 3초 내 핵심 제시"
        if performance.engagement_rate < 0.05:
            return "CTA를 더 자연스럽게, 질문형으로"
        ...
```

### 4.2 Multi-Platform Publishing

```python
# 한 번 제작, 여러 플랫폼 배포
class MultiPublisher:
    """YouTube, TikTok, Instagram Reels 동시 배포"""

    platforms = {
        "youtube": YouTubePublisher(),
        "tiktok": TikTokPublisher(),      # 향후 확장
        "instagram": InstagramPublisher(), # 향후 확장
    }

    async def publish_all(self, video: Video, platforms: list[str]):
        results = await asyncio.gather(*[
            self.platforms[p].publish(video)
            for p in platforms
        ])
        return dict(zip(platforms, results))
```

### 4.3 A/B Thumbnail Testing

```python
# 썸네일 A/B 테스트 자동화
class ThumbnailOptimizer:
    async def create_variants(self, video: Video) -> list[Thumbnail]:
        """동일 콘텐츠에 대해 3가지 썸네일 생성"""
        return [
            await self.generate_thumbnail(video, style="minimal"),
            await self.generate_thumbnail(video, style="dramatic"),
            await self.generate_thumbnail(video, style="viral"),
        ]

    async def run_ab_test(self, video_id: str, thumbnails: list[Thumbnail]):
        """7일간 썸네일 교체하며 CTR 측정"""
        for i, thumb in enumerate(thumbnails):
            await self.youtube.update_thumbnail(video_id, thumb)
            await asyncio.sleep(days(2))
            thumb.ctr = await self.get_ctr(video_id)

        best = max(thumbnails, key=lambda t: t.ctr)
        await self.youtube.update_thumbnail(video_id, best)
```

### 4.4 Voice Consistency System

```python
# 사용자 음성 프로파일 학습 (직접 녹음 워크플로우)
class VoiceProfiler:
    """사용자 녹음을 분석하여 일관된 스타일 유지"""

    async def analyze_voice(self, audio_samples: list[Path]) -> VoiceProfile:
        """녹음 샘플에서 특성 추출"""
        profiles = [
            await self.extract_features(sample)
            for sample in audio_samples
        ]
        return VoiceProfile(
            avg_speed=mean([p.speed for p in profiles]),
            pitch_range=(min(p.min_pitch), max(p.max_pitch)),
            pause_duration=mean([p.pause_duration for p in profiles]),
        )

    def generate_recording_guide(self, script: Script, profile: VoiceProfile) -> RecordingGuide:
        """녹음 가이드 생성"""
        return RecordingGuide(
            target_duration=script.estimated_duration,
            recommended_speed=profile.avg_speed,
            pause_markers=script.get_pause_points(),
        )
```

### 4.5 Smart Scheduling

```python
# 최적 업로드 시간 학습
class SmartScheduler:
    async def analyze_audience(self, channel_id: str) -> AudiencePattern:
        """채널 시청자 활동 패턴 분석"""
        analytics = await self.youtube.get_audience_retention()
        return AudiencePattern(
            peak_hours=[hour for hour, views in analytics if views > avg],
            peak_days=self._find_peak_days(analytics),
        )

    def suggest_schedule(self, pattern: AudiencePattern, videos: list[Video]) -> Schedule:
        """최적 업로드 스케줄 생성"""
        schedule = []
        for video in videos:
            best_slot = self._find_next_peak(pattern, schedule)
            schedule.append((video, best_slot))
        return schedule
```

---

## Part 5: 올빼미 프로젝트 통합

### 5.1 재사용할 서비스

```python
# 올빼미에서 가져올 검증된 코드
REUSE_FROM_OLBAEMI = {
    "youtube_uploader.py": "OAuth 토큰 관리, 이어받기 업로드",
    "thumbnail_generator.py": "템플릿/AI/바이럴 썸네일 생성",
    "seo_optimizer.py": "제목/설명/태그/해시태그 최적화",
    "llm.py": "멀티 프로바이더 LLM 지원",
}
```

### 5.2 통합 방법

```python
# infrastructure/youtube/youtube_api_adapter.py
# 올빼미의 youtube_uploader.py를 리팩터링하여 통합

from stoicflow.application.interfaces.publisher import Publisher
from stoicflow.domain.entities import Video, VideoMetadata

class YouTubeAPIAdapter(Publisher):
    """올빼미 youtube_uploader.py 기반, Clean Architecture 적합하게 리팩터"""

    def __init__(self, credentials_path: Path, token_storage: Path):
        self.credentials_path = credentials_path
        self.token_storage = token_storage
        self._youtube = None

    async def authenticate(self, user_id: str) -> bool:
        """올빼미의 get_credentials 로직"""
        token_path = self.token_storage / f"{user_id}_youtube_token.json"
        # ... 올빼미 코드 재사용

    async def publish(self, video: Video, metadata: VideoMetadata) -> str:
        """올빼미의 upload_video 로직 + async 변환"""
        # ... Resumable upload 구현
```

---

## Part 6: Configuration (Pydantic Settings)

```python
# src/stoicflow/config/settings.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 설정
    llm_provider: str = Field(default="claude", description="claude|gemini|ollama")
    anthropic_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    ollama_host: str = "http://localhost:11434"

    # TTS 설정
    tts_provider: str = Field(default="edge", description="edge|elevenlabs|skip")
    elevenlabs_api_key: SecretStr | None = None
    edge_voice: str = "ko-KR-SunHiNeural"  # 한국어 기본 음성

    # 비디오 설정
    video_width: int = 1080
    video_height: int = 1920
    fps: int = 30
    background_music_volume: float = 0.1

    # YouTube 설정
    youtube_client_secrets: str = "client_secret.json"
    youtube_default_privacy: str = "private"
    youtube_default_category: str = "22"  # People & Blogs

    # 경로 설정
    data_dir: str = "data"
    output_dir: str = "data/output"
    scripts_dir: str = "data/scripts"

settings = Settings()
```

```bash
# .env.example
# LLM (하나만 설정하면 됨)
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-xxx

# TTS (선택 - 기본값: edge 무료)
TTS_PROVIDER=edge
# ELEVENLABS_API_KEY=xxx  # 프리미엄 사용시

# 미디어 (선택)
# PEXELS_API_KEY=xxx  # 스톡 비디오 사용시

# YouTube (필수 - 업로드시)
# client_secret.json 파일 필요
```

---

## Part 7: Implementation Plan

### Phase 1: Foundation (Week 1-2)

```
□ 프로젝트 초기화 (uv, pyproject.toml)
□ Domain Layer 구현
  - Script, Video, Channel 엔티티
  - AudioClip, Subtitle Value Objects
□ Configuration 설정 (Pydantic Settings)
□ 기본 CLI 스캐폴딩 (Typer)
```

### Phase 2: Core Pipeline (Week 3-4)

```
□ LLM Provider 추상화 + Claude Adapter
□ TTS Provider 추상화 + EdgeTTS Adapter
□ VideoEditor 추상화 + MoviePy Adapter
□ Pipeline Service 구현 (오케스트레이션)
□ 기본 워크플로우 테스트
```

### Phase 3: YouTube Integration (Week 5)

```
□ 올빼미 youtube_uploader.py 마이그레이션
□ OAuth 플로우 개선
□ SEO Optimizer 통합
□ Thumbnail Generator 통합
```

### Phase 4: UI Layer (Week 6)

```
□ CLI 완성 (전체 커맨드)
□ Flet GUI 또는 Textual TUI 구현
□ 녹음 가이드 생성 기능
□ 프리뷰 기능
```

### Phase 5: Advanced Features (Week 7+)

```
□ A/B Thumbnail Testing
□ Smart Scheduling
□ Performance Analytics
□ Multi-Platform 확장 준비
```

---

## Part 8: CLI Interface Design

```bash
# 기본 사용법
stoicflow generate              # 대화형으로 쇼츠 생성
stoicflow generate --script 1   # 특정 스크립트로 생성

# 스크립트 관리
stoicflow scripts list          # 스크립트 목록
stoicflow scripts new           # AI로 새 스크립트 생성
stoicflow scripts show 1        # 스크립트 상세 보기

# 녹음 워크플로우
stoicflow record 1              # 스크립트 1번 녹음 가이드 표시
stoicflow record 1 --check      # 녹음 파일 체크

# 비디오 생성
stoicflow compose 1             # 비디오 컴포지션
stoicflow compose 1 --preview   # 프리뷰만

# 업로드
stoicflow upload video.mp4      # YouTube 업로드
stoicflow schedule              # 스마트 스케줄링

# GUI/TUI 실행
stoicflow gui                   # Flet GUI 실행
stoicflow tui                   # Textual TUI 실행
```

---

## Part 9: Key Differentiators

| 기능 | 기존 프로젝트들 | StoicFlow |
|------|---------------|-----------|
| **아키텍처** | 모놀리식, 스파게티 | Clean Architecture |
| **패키지 관리** | pip, poetry | uv (10-100x 빠름) |
| **Python** | 3.10-3.11 | 3.13+ (JIT, 성능 향상) |
| **LLM** | 단일 프로바이더 | 멀티 프로바이더 (Claude/Gemini/Ollama) |
| **TTS** | 유료 API만 | 무료 기본 (EdgeTTS) + 유료 옵션 |
| **음성** | AI TTS 전용 | 직접 녹음 워크플로우 지원 |
| **UI** | 없음 또는 Gradio | CLI + GUI (Flet) + TUI (Textual) |
| **설정** | 하드코딩 | Pydantic Settings (.env) |
| **업로드** | 기본 | Resumable + 스마트 스케줄링 |
| **분석** | 없음 | 성과 기반 스크립트 개선 |

---

## Sources & References

### GitHub Projects
- [ShortGPT](https://github.com/RayVentura/ShortGPT) - Engine 패턴, 멀티 언어
- [MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) - 심플 UX, 12K+ stars
- [AI-Youtube-Shorts-Generator](https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator) - GPU 가속, CV
- [auto-shorts](https://github.com/alamshafil/auto-shorts) - LLM 추상화, 오프라인 대안
- [auto-yt-shorts](https://github.com/marvinvr/auto-yt-shorts) - FastAPI, Docker
- [short-video-maker](https://github.com/gyoridavid/short-video-maker) - MCP 통합

### 2026 Python Ecosystem
- [uv Package Manager](https://github.com/astral-sh/uv) - Rust 기반, 초고속
- [Python 3.13](https://docs.python.org/3.13/whatsnew/3.13.html) - JIT, free-threading
- [Pydantic v2](https://docs.pydantic.dev/) - 설정 관리
- [Flet](https://flet.dev/) - Flutter 기반 Python GUI
- [Textual](https://textual.textualize.io/) - 모던 TUI

### Video & Audio
- [MoviePy 2.x](https://zulko.github.io/moviepy/) - 비디오 편집
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - GPU 가속 STT
- [EdgeTTS](https://github.com/rany2/edge-tts) - 무료 한국어 TTS
