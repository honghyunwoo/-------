# 기술 설계서 (Technical Design Document)
# Shorts Factory - 시스템 아키텍처 및 구현 설계

---

## 1. 시스템 아키텍처

### 1.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Shorts Factory 아키텍처                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                         CLI Layer                             │  │
│  │                        (main.py)                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                     │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Pipeline Orchestrator                    │  │
│  │                      (pipeline.py)                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                     │
│         ┌─────────────────────┼─────────────────────┐              │
│         │                     │                     │              │
│         ▼                     ▼                     ▼              │
│  ┌────────────┐       ┌────────────┐       ┌────────────┐         │
│  │  Content   │       │   Audio    │       │   Video    │         │
│  │  Module    │       │   Module   │       │   Module   │         │
│  └────────────┘       └────────────┘       └────────────┘         │
│         │                     │                     │              │
│         ▼                     ▼                     ▼              │
│  ┌────────────┐       ┌────────────┐       ┌────────────┐         │
│  │ - quote    │       │ - tts      │       │ - broll    │         │
│  │ - script   │       │ - subtitle │       │ - composer │         │
│  │ - review   │       │            │       │            │         │
│  │ - metadata │       │            │       │            │         │
│  └────────────┘       └────────────┘       └────────────┘         │
│         │                     │                     │              │
│         └─────────────────────┼─────────────────────┘              │
│                               │                                     │
│                               ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      External Services                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │ Claude   │  │TYPECAST  │  │ElevenLabs│  │  Local   │      │  │
│  │  │   API    │  │   API    │  │   API    │  │  Files   │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 디렉토리 구조

```
/shorts-factory/
│
├── main.py                     # CLI 진입점
├── pipeline.py                 # 파이프라인 오케스트레이터
├── requirements.txt            # 의존성
├── setup.py                    # 패키지 설정
│
├── /core/                      # 핵심 모듈
│   ├── __init__.py
│   ├── quote_loader.py         # 명언 로드
│   ├── script_generator.py     # 스크립트 생성
│   ├── review_loop.py          # 재검토 루프
│   ├── tts_engine.py           # TTS 엔진
│   ├── subtitle_generator.py   # 자막 생성
│   ├── broll_selector.py       # B-roll 선택
│   ├── video_composer.py       # 영상 합성
│   └── metadata_generator.py   # 메타데이터 생성
│
├── /models/                    # 데이터 모델
│   ├── __init__.py
│   ├── quote.py
│   ├── script.py
│   └── video.py
│
├── /templates/                 # 콘텐츠 템플릿
│   ├── /stoic/
│   │   ├── quotes_library.json
│   │   ├── hook_templates.json
│   │   ├── cta_templates.json
│   │   └── prompts.yaml
│   └── /english/
│       ├── expressions_library.json
│       └── prompts.yaml
│
├── /assets/                    # 정적 리소스
│   ├── /bgm/
│   │   ├── epic_01.mp3
│   │   └── piano_01.mp3
│   ├── /fonts/
│   │   └── NotoSerifKR-Bold.ttf
│   └── /b-roll/
│       ├── /nature/
│       ├── /city/
│       └── /abstract/
│
├── /config/                    # 설정
│   ├── settings.yaml
│   └── .env.example
│
├── /output/                    # 출력물
│   └── {YYYY-MM-DD}_{title}/
│
├── /tests/                     # 테스트
│   ├── test_quote_loader.py
│   ├── test_script_generator.py
│   └── test_pipeline.py
│
└── /docs/                      # 문서
    ├── 01_PRD.md
    ├── 02_MVP.md
    ├── 03_5W1H.md
    ├── 04_TECHNICAL_DESIGN.md
    ├── 05_CONTENT_GUIDELINE.md
    └── 06_OPERATIONS_SOP.md
```

---

## 2. 모듈 상세 설계

### 2.1 quote_loader.py

```python
"""
명언 로더 모듈
quotes_library.json에서 명언을 로드하고 관리
"""

from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class Quote:
    id: int
    text: str
    author: str
    source: str
    themes: List[str]
    used_count: int = 0
    last_used: Optional[str] = None

class QuoteLoader:
    def __init__(self, library_path: str):
        self.library_path = library_path
        self.quotes = self._load_library()

    def _load_library(self) -> List[Quote]:
        """JSON 파일에서 명언 라이브러리 로드"""
        pass

    def get_by_id(self, quote_id: int) -> Quote:
        """ID로 명언 조회"""
        pass

    def get_random(self, theme: Optional[str] = None) -> Quote:
        """랜덤 명언 선택 (테마 필터 가능)"""
        pass

    def get_unused(self, limit: int = 10) -> List[Quote]:
        """사용하지 않은 명언 목록"""
        pass

    def mark_used(self, quote_id: int) -> None:
        """명언 사용 표시"""
        pass
```

### 2.2 script_generator.py

```python
"""
스크립트 생성 모듈
Claude API를 사용하여 명언 기반 스크립트 생성
"""

from dataclasses import dataclass
from typing import Literal
import anthropic

HookType = Literal["H1", "H2", "H3", "H4", "H5"]
CTAType = Literal["C1", "C2", "C3", "C4", "C5"]

@dataclass
class Script:
    id: str
    quote_id: int
    hook: str
    quote_text: str
    explanation: str
    example: str
    cta: str
    full_text: str
    hook_type: HookType
    cta_type: CTAType
    review_score: float = 0.0

class ScriptGenerator:
    def __init__(self, api_key: str, prompts_path: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompts = self._load_prompts(prompts_path)

    def generate(
        self,
        quote: Quote,
        hook_type: HookType = "H1",
        cta_type: CTAType = "C3"
    ) -> Script:
        """스크립트 생성"""
        prompt = self._build_prompt(quote, hook_type, cta_type)
        response = self._call_api(prompt)
        return self._parse_response(response, quote, hook_type, cta_type)

    def _build_prompt(self, quote: Quote, hook_type: HookType, cta_type: CTAType) -> str:
        """프롬프트 구성"""
        pass

    def _call_api(self, prompt: str) -> str:
        """Claude API 호출"""
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    def _parse_response(self, response: str, quote: Quote, hook_type: HookType, cta_type: CTAType) -> Script:
        """API 응답 파싱"""
        pass
```

### 2.3 review_loop.py

```python
"""
재검토 루프 모듈
생성된 스크립트를 평가하고 개선
"""

from dataclasses import dataclass
from typing import Tuple
import anthropic

@dataclass
class ReviewResult:
    hook_score: float
    accuracy_score: float
    clarity_score: float
    cta_score: float
    flow_score: float
    average: float
    feedback: str
    improved_script: Optional[Script] = None

class ReviewLoop:
    MIN_SCORE = 8.0
    MAX_ITERATIONS = 3

    def __init__(self, api_key: str, prompts_path: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompts = self._load_prompts(prompts_path)

    def review_and_improve(self, script: Script) -> Script:
        """스크립트 검토 및 개선"""
        for i in range(self.MAX_ITERATIONS):
            result = self._evaluate(script)
            script.review_score = result.average

            if result.average >= self.MIN_SCORE:
                return script

            script = self._improve(script, result.feedback)

        return script  # 최대 반복 후 반환

    def _evaluate(self, script: Script) -> ReviewResult:
        """스크립트 평가"""
        pass

    def _improve(self, script: Script, feedback: str) -> Script:
        """피드백 기반 개선"""
        pass
```

### 2.4 tts_engine.py

```python
"""
TTS 엔진 모듈
텍스트를 음성으로 변환 (TYPECAST, ElevenLabs)
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

class TTSProvider(Enum):
    TYPECAST = "typecast"
    ELEVENLABS = "elevenlabs"

class BaseTTSEngine(ABC):
    @abstractmethod
    def generate(self, text: str, output_path: Path) -> Path:
        pass

class TypecastEngine(BaseTTSEngine):
    def __init__(self, api_key: str, voice_id: str = "default"):
        self.api_key = api_key
        self.voice_id = voice_id

    def generate(self, text: str, output_path: Path) -> Path:
        """TYPECAST API로 TTS 생성"""
        pass

class ElevenLabsEngine(BaseTTSEngine):
    def __init__(self, api_key: str, voice_id: str = "default"):
        self.api_key = api_key
        self.voice_id = voice_id

    def generate(self, text: str, output_path: Path) -> Path:
        """ElevenLabs API로 TTS 생성"""
        pass

class TTSEngine:
    def __init__(self, provider: TTSProvider, api_key: str, voice_id: str = "default"):
        if provider == TTSProvider.TYPECAST:
            self.engine = TypecastEngine(api_key, voice_id)
        else:
            self.engine = ElevenLabsEngine(api_key, voice_id)

    def generate(self, text: str, output_path: Path) -> Path:
        return self.engine.generate(text, output_path)
```

### 2.5 subtitle_generator.py

```python
"""
자막 생성 모듈
스크립트 기반 SRT 자막 파일 생성
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
import re

@dataclass
class SubtitleEntry:
    index: int
    start_time: str  # "00:00:00,000"
    end_time: str
    text: str

class SubtitleGenerator:
    MAX_CHARS_PER_LINE = 15  # 한글 기준

    def __init__(self):
        pass

    def generate_from_script(
        self,
        script: Script,
        audio_duration: float,
        output_path: Path
    ) -> Path:
        """스크립트 기반 자막 생성"""
        sentences = self._split_sentences(script.full_text)
        entries = self._calculate_timings(sentences, audio_duration)
        return self._write_srt(entries, output_path)

    def generate_from_audio(
        self,
        audio_path: Path,
        output_path: Path
    ) -> Path:
        """Whisper로 오디오에서 자막 추출"""
        pass

    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리"""
        pass

    def _calculate_timings(self, sentences: List[str], total_duration: float) -> List[SubtitleEntry]:
        """문장별 타이밍 계산"""
        pass

    def _write_srt(self, entries: List[SubtitleEntry], output_path: Path) -> Path:
        """SRT 파일 작성"""
        pass
```

### 2.6 broll_selector.py

```python
"""
B-roll 선택 모듈
테마 기반 배경 영상 선택
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import random

@dataclass
class BrollClip:
    path: Path
    duration: float
    themes: List[str]

class BrollSelector:
    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.clips = self._scan_clips()

    def _scan_clips(self) -> List[BrollClip]:
        """B-roll 폴더 스캔"""
        pass

    def select(
        self,
        themes: List[str],
        target_duration: float
    ) -> List[BrollClip]:
        """테마에 맞는 클립 선택"""
        matching = [c for c in self.clips if any(t in c.themes for t in themes)]

        if not matching:
            matching = self.clips  # 매칭 없으면 전체에서 선택

        selected = []
        total = 0.0

        while total < target_duration and matching:
            clip = random.choice(matching)
            selected.append(clip)
            total += clip.duration

        return selected
```

### 2.7 video_composer.py

```python
"""
영상 합성 모듈
오디오 + B-roll + 자막 → 최종 영상
(기존 video.py에서 추출 및 수정)
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, concatenate_videoclips
)

@dataclass
class CompositionConfig:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    bgm_volume: float = 0.2
    subtitle_font: str = "NotoSerifKR-Bold"
    subtitle_fontsize: int = 48
    subtitle_color: str = "white"
    highlight_color: str = "gold"

class VideoComposer:
    def __init__(self, config: CompositionConfig = None):
        self.config = config or CompositionConfig()

    def compose(
        self,
        audio_path: Path,
        broll_clips: List[BrollClip],
        srt_path: Path,
        bgm_path: Optional[Path] = None,
        output_path: Path = None
    ) -> Path:
        """영상 합성"""
        # 1. 오디오 로드
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        # 2. B-roll 연결
        video = self._concatenate_broll(broll_clips, duration)

        # 3. 9:16 리사이즈
        video = self._resize_to_vertical(video)

        # 4. 오디오 합성
        video = video.set_audio(audio)

        # 5. BGM 믹싱
        if bgm_path:
            video = self._add_bgm(video, bgm_path)

        # 6. 자막 오버레이
        video = self._add_subtitles(video, srt_path)

        # 7. 렌더링
        video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec='libx264',
            audio_codec='aac'
        )

        return output_path

    def _concatenate_broll(self, clips: List[BrollClip], target_duration: float) -> VideoFileClip:
        """B-roll 클립 연결"""
        pass

    def _resize_to_vertical(self, video: VideoFileClip) -> VideoFileClip:
        """9:16 비율로 리사이즈"""
        pass

    def _add_bgm(self, video: VideoFileClip, bgm_path: Path) -> VideoFileClip:
        """BGM 추가"""
        pass

    def _add_subtitles(self, video: VideoFileClip, srt_path: Path) -> VideoFileClip:
        """자막 오버레이"""
        pass
```

### 2.8 metadata_generator.py

```python
"""
메타데이터 생성 모듈
YouTube 업로드용 제목, 설명, 태그 생성
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
import json

@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    category: str = "22"  # People & Blogs

class MetadataGenerator:
    def __init__(self, templates_path: Path):
        self.templates = self._load_templates(templates_path)

    def generate(self, script: Script, channel: str = "stoic") -> VideoMetadata:
        """메타데이터 생성"""
        template = self.templates[channel]

        title = self._generate_title(script, template)
        description = self._generate_description(script, template)
        tags = self._generate_tags(script, template)
        hashtags = self._generate_hashtags(script, template)

        return VideoMetadata(
            title=title,
            description=description,
            tags=tags,
            hashtags=hashtags
        )

    def save(self, metadata: VideoMetadata, output_path: Path) -> Path:
        """JSON으로 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.__dict__, f, ensure_ascii=False, indent=2)
        return output_path
```

---

## 3. 파이프라인 설계

### 3.1 pipeline.py

```python
"""
파이프라인 오케스트레이터
전체 영상 생성 프로세스 조율
"""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging

@dataclass
class PipelineResult:
    success: bool
    video_path: Optional[Path]
    audio_path: Optional[Path]
    srt_path: Optional[Path]
    metadata_path: Optional[Path]
    script: Optional[Script]
    error: Optional[str] = None
    duration_seconds: float = 0.0

class Pipeline:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self._init_modules()

    def _init_modules(self):
        """모듈 초기화"""
        self.quote_loader = QuoteLoader(self.config.quotes_path)
        self.script_generator = ScriptGenerator(
            self.config.claude_api_key,
            self.config.prompts_path
        )
        self.review_loop = ReviewLoop(
            self.config.claude_api_key,
            self.config.prompts_path
        )
        self.tts_engine = TTSEngine(
            self.config.tts_provider,
            self.config.tts_api_key
        )
        self.subtitle_gen = SubtitleGenerator()
        self.broll_selector = BrollSelector(self.config.broll_path)
        self.video_composer = VideoComposer()
        self.metadata_gen = MetadataGenerator(self.config.templates_path)

    def run(
        self,
        quote_id: int,
        hook_type: str = "H1",
        cta_type: str = "C3",
        channel: str = "stoic"
    ) -> PipelineResult:
        """파이프라인 실행"""
        start_time = datetime.now()
        output_dir = self._create_output_dir()

        try:
            # 1. 명언 로드
            quote = self.quote_loader.get_by_id(quote_id)
            logging.info(f"명언 로드: {quote.text[:30]}...")

            # 2. 스크립트 생성
            script = self.script_generator.generate(quote, hook_type, cta_type)
            logging.info(f"스크립트 생성 완료")

            # 3. 재검토 루프
            script = self.review_loop.review_and_improve(script)
            logging.info(f"재검토 완료 (점수: {script.review_score})")

            # 4. TTS 생성
            audio_path = output_dir / "audio.mp3"
            self.tts_engine.generate(script.full_text, audio_path)
            logging.info(f"TTS 생성 완료")

            # 5. 자막 생성
            srt_path = output_dir / "captions.srt"
            audio_duration = self._get_audio_duration(audio_path)
            self.subtitle_gen.generate_from_script(script, audio_duration, srt_path)
            logging.info(f"자막 생성 완료")

            # 6. B-roll 선택
            broll_clips = self.broll_selector.select(quote.themes, audio_duration)
            logging.info(f"B-roll 선택 완료 ({len(broll_clips)}개)")

            # 7. 영상 합성
            video_path = output_dir / "video.mp4"
            bgm_path = self._select_bgm(quote.themes)
            self.video_composer.compose(
                audio_path, broll_clips, srt_path, bgm_path, video_path
            )
            logging.info(f"영상 합성 완료")

            # 8. 메타데이터 생성
            metadata = self.metadata_gen.generate(script, channel)
            metadata_path = output_dir / "metadata.json"
            self.metadata_gen.save(metadata, metadata_path)
            logging.info(f"메타데이터 생성 완료")

            # 9. 명언 사용 표시
            self.quote_loader.mark_used(quote_id)

            duration = (datetime.now() - start_time).total_seconds()

            return PipelineResult(
                success=True,
                video_path=video_path,
                audio_path=audio_path,
                srt_path=srt_path,
                metadata_path=metadata_path,
                script=script,
                duration_seconds=duration
            )

        except Exception as e:
            logging.error(f"파이프라인 오류: {e}")
            return PipelineResult(
                success=False,
                error=str(e),
                video_path=None,
                audio_path=None,
                srt_path=None,
                metadata_path=None,
                script=None
            )
```

---

## 4. 설정 파일 설계

### 4.1 settings.yaml

```yaml
# Shorts Factory 설정

# 채널 설정
channels:
  stoic:
    name: "매일 스토아"
    language: "ko"
    tts_provider: "typecast"
    tts_voice_id: "your-voice-id"
    themes: ["philosophy", "motivation", "self-improvement"]

  english:
    name: "English Shorts"
    language: "en"
    tts_provider: "elevenlabs"
    tts_voice_id: "your-voice-id"
    themes: ["english", "learning", "expressions"]

# 영상 설정
video:
  width: 1080
  height: 1920
  fps: 30
  codec: "libx264"
  audio_codec: "aac"
  bitrate: "5M"

# 자막 설정
subtitle:
  font: "NotoSerifKR-Bold"
  fontsize: 48
  color: "white"
  highlight_color: "gold"
  position: "bottom"
  max_chars_per_line: 15

# BGM 설정
bgm:
  volume: 0.2
  fade_duration: 1.0

# 경로 설정
paths:
  assets: "./assets"
  templates: "./templates"
  output: "./output"
  fonts: "./assets/fonts"
  bgm: "./assets/bgm"
  broll: "./assets/b-roll"

# 파이프라인 설정
pipeline:
  review_min_score: 8.0
  review_max_iterations: 3
  default_hook_type: "H1"
  default_cta_type: "C3"

# 로깅 설정
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/shorts-factory.log"
```

### 4.2 .env.example

```bash
# API Keys
CLAUDE_API_KEY=your-claude-api-key
TYPECAST_API_KEY=your-typecast-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Optional
YOUTUBE_API_KEY=your-youtube-api-key
```

---

## 5. 의존성

### 5.1 requirements.txt

```
# Core
anthropic>=0.18.0
python-dotenv>=1.0.0
pyyaml>=6.0

# Video/Audio Processing
moviepy>=1.0.3
pydub>=0.25.1
Pillow>=10.0.0

# TTS
requests>=2.31.0

# Subtitle
faster-whisper>=0.10.0

# Utils
click>=8.1.0
rich>=13.0.0
tqdm>=4.66.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## 6. 에러 처리

### 6.1 예외 정의

```python
# exceptions.py

class ShortsFactoryError(Exception):
    """기본 예외"""
    pass

class QuoteNotFoundError(ShortsFactoryError):
    """명언을 찾을 수 없음"""
    pass

class ScriptGenerationError(ShortsFactoryError):
    """스크립트 생성 실패"""
    pass

class TTSError(ShortsFactoryError):
    """TTS 생성 실패"""
    pass

class VideoCompositionError(ShortsFactoryError):
    """영상 합성 실패"""
    pass

class APIError(ShortsFactoryError):
    """외부 API 오류"""
    pass
```

### 6.2 재시도 로직

```python
# utils/retry.py

import time
from functools import wraps

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
```

---

## 7. 테스트 전략

### 7.1 단위 테스트

```python
# tests/test_quote_loader.py

import pytest
from core.quote_loader import QuoteLoader, Quote

class TestQuoteLoader:
    def test_load_existing_quote(self):
        loader = QuoteLoader("templates/stoic/quotes_library.json")
        quote = loader.get_by_id(1)
        assert isinstance(quote, Quote)
        assert quote.id == 1

    def test_load_nonexistent_quote(self):
        loader = QuoteLoader("templates/stoic/quotes_library.json")
        with pytest.raises(QuoteNotFoundError):
            loader.get_by_id(99999)

    def test_get_random_quote(self):
        loader = QuoteLoader("templates/stoic/quotes_library.json")
        quote = loader.get_random()
        assert isinstance(quote, Quote)
```

### 7.2 통합 테스트

```python
# tests/test_pipeline.py

import pytest
from pipeline import Pipeline

class TestPipeline:
    def test_full_pipeline(self):
        pipeline = Pipeline("config/settings.yaml")
        result = pipeline.run(quote_id=1)

        assert result.success
        assert result.video_path.exists()
        assert result.duration_seconds < 300  # 5분 이내
```

---

## 8. 보안 고려사항

| 항목 | 조치 |
|-----|-----|
| API 키 | .env 파일로 관리, .gitignore 추가 |
| 출력물 | 민감 정보 포함 금지 |
| 로깅 | API 키 로깅 금지 |
| 의존성 | 정기적 보안 업데이트 |

---

*문서 끝*
