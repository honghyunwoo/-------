# Shorts Factory API Reference

> **핵심 모듈 API 문서**

---

## 목차

1. [QuoteLoader](#quoteloader)
2. [ScriptGenerator](#scriptgenerator)
3. [TTSEngine](#ttsengine)
4. [SubtitleGenerator](#subtitlegenerator)
5. [BrollSelector](#brollselector)
6. [VideoComposer](#videocomposer)
7. [MetadataGenerator](#metadatagenerator)

---

## QuoteLoader

**파일**: `core/quote_loader.py`

명언 라이브러리 로드 및 관리.

### Quote (Dataclass)

```python
@dataclass
class Quote:
    id: int                     # 명언 ID
    text: str                   # 명언 텍스트 (한국어)
    author: str                 # 저자명
    source: str                 # 출처
    themes: List[str]           # 테마 목록
    text_original: str = ""     # 원문 (영어)
    author_en: str = ""         # 저자명 (영어)
    used_count: int = 0         # 사용 횟수
    last_used: Optional[str]    # 마지막 사용일
```

### QuoteLoader

```python
class QuoteLoader:
    def __init__(self, library_path: str | Path):
        """명언 라이브러리 초기화"""

    def get_by_id(self, quote_id: int) -> Quote:
        """ID로 명언 조회"""

    def get_random(self) -> Quote:
        """랜덤 명언 반환"""

    def get_unused(self, limit: int = 5) -> List[Quote]:
        """미사용 명언 목록 (used_count=0 우선)"""

    def get_by_theme(self, theme: str) -> List[Quote]:
        """테마별 명언 조회"""

    def mark_used(self, quote_id: int) -> None:
        """사용 표시 (used_count 증가)"""

    def list_all(self) -> List[Quote]:
        """전체 명언 목록"""

    def get_stats(self) -> Dict:
        """통계 반환 {total, used, unused}"""

    def count(self) -> int:
        """총 명언 수"""
```

---

## ScriptGenerator

**파일**: `core/script_generator.py`

Gemini API를 사용한 스크립트 생성.

### ScriptGenerator

```python
class ScriptGenerator:
    def __init__(self, api_key: str = None):
        """Gemini API 키로 초기화"""

    def generate(
        self,
        quote: Quote,
        style: str = "cinematic",
        target_duration: int = 30
    ) -> Dict[str, str]:
        """스크립트 생성

        Returns:
            {
                "hook": "질문형 오프닝...",
                "quote": "명언 원문...",
                "explanation": "해설...",
                "application": "현대 적용...",
                "cta": "마무리..."
            }
        """

    def generate_tts_text(self, script: Dict[str, str]) -> str:
        """TTS용 전체 텍스트 생성"""
```

---

## TTSEngine

**파일**: `core/tts_engine.py`

Edge TTS를 사용한 음성 합성.

### TTSConfig (Dataclass)

```python
@dataclass
class TTSConfig:
    voice: str = "ko-KR-SunHiNeural"  # 한국어 여성
    rate: str = "+0%"                  # 속도
    pitch: str = "+0Hz"                # 음높이
    volume: str = "+0%"                # 볼륨
```

### TTSEngine

```python
class TTSEngine:
    def __init__(self, config: TTSConfig = None):
        """TTS 엔진 초기화"""

    async def generate(
        self,
        text: str,
        output_path: Path
    ) -> Path:
        """음성 파일 생성 (MP3)"""

    async def generate_with_timing(
        self,
        text: str,
        output_path: Path
    ) -> Tuple[Path, List[Dict]]:
        """음성 + 단어별 타이밍 데이터"""

    def get_available_voices(self) -> List[str]:
        """사용 가능한 음성 목록"""
```

---

## SubtitleGenerator

**파일**: `core/subtitle_generator.py`

SRT 자막 파일 생성 및 파싱.

### SubtitleEntry (Dataclass)

```python
@dataclass
class SubtitleEntry:
    index: int          # 자막 번호
    start_time: float   # 시작 시간 (초)
    end_time: float     # 종료 시간 (초)
    text: str           # 자막 텍스트

    def to_srt(self) -> str:
        """SRT 형식 문자열 반환"""

    def to_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 형식으로 변환 (00:00:00,000)"""
```

### SubtitleConfig (Dataclass)

```python
@dataclass
class SubtitleConfig:
    max_chars_per_line: int = 15  # 줄당 최대 글자
    max_lines: int = 2            # 최대 줄 수
    min_duration: float = 1.0     # 최소 표시 시간
```

### SubtitleGenerator

```python
class SubtitleGenerator:
    def __init__(self, config: SubtitleConfig = None):
        """자막 생성기 초기화"""

    def generate_from_script(
        self,
        script: str,
        total_duration: float,
        output_path: Path
    ) -> Path:
        """스크립트에서 SRT 파일 생성"""

    def parse_srt(self, srt_path: Path) -> List[SubtitleEntry]:
        """SRT 파일 파싱"""
```

---

## BrollSelector

**파일**: `core/broll_selector.py`

테마 기반 B-roll 클립 선택.

### BrollClip (Dataclass)

```python
@dataclass
class BrollClip:
    path: Path              # 파일 경로
    duration: float         # 길이 (초)
    themes: List[str]       # 테마 목록
    source: str = ""        # 출처 (pexels, pixabay)
    resolution: str = ""    # 해상도

    def to_dict(self) -> dict:
        """딕셔너리 변환"""

    @classmethod
    def from_dict(cls, data: dict) -> 'BrollClip':
        """딕셔너리에서 생성"""
```

### BrollSelector

```python
class BrollSelector:
    THEME_KEYWORDS = {
        "역경": ["mountain", "storm", "rain"],
        "마음": ["meditation", "peace", "calm"],
        # ... 더 많은 테마
    }

    def __init__(
        self,
        config: BrollConfig = None,
        assets_path: Path = None
    ):
        """B-roll 선택기 초기화"""

    def select(
        self,
        themes: List[str],
        target_duration: float,
        avoid_repeats: bool = True
    ) -> List[BrollClip]:
        """테마에 맞는 클립 선택"""

    def select_by_category(
        self,
        category: str,
        target_duration: float
    ) -> List[BrollClip]:
        """카테고리별 클립 선택"""

    def get_stats(self) -> Dict:
        """통계 반환 {total_clips, total_duration, themes, avg_duration}"""

    def save_index(self) -> None:
        """인덱스 파일 저장"""

    def refresh_index(self) -> None:
        """폴더 재스캔 및 인덱스 갱신"""
```

### BrollDownloader

```python
class BrollDownloader:
    def __init__(
        self,
        output_path: Path,
        pexels_key: str = None
    ):
        """B-roll 다운로더 초기화"""

    def search_pexels(
        self,
        query: str,
        per_page: int = 5
    ) -> List[dict]:
        """Pexels에서 비디오 검색"""

    def download_video(
        self,
        url: str,
        filename: str,
        category: str = "general"
    ) -> Optional[Path]:
        """비디오 다운로드"""
```

---

## VideoComposer

**파일**: `core/video_composer.py`

최종 영상 합성.

### CompositionConfig (Dataclass)

```python
@dataclass
class CompositionConfig:
    width: int = 1080               # 영상 너비
    height: int = 1920              # 영상 높이 (9:16)
    fps: int = 30                   # 프레임레이트
    codec: str = "libx264"          # 비디오 코덱
    audio_codec: str = "aac"        # 오디오 코덱
    bitrate: str = "5M"             # 비트레이트

    bgm_volume: float = 0.2         # BGM 볼륨
    bgm_fade_in: float = 1.0        # BGM 페이드 인
    bgm_fade_out: float = 2.0       # BGM 페이드 아웃

    subtitle_font: str = "..."      # 자막 폰트
    subtitle_fontsize: int = 48     # 자막 크기
    subtitle_color: str = "white"   # 자막 색상
    subtitle_bottom_margin: int = 320  # 하단 여백
    subtitle_text_margin: int = 20  # 텍스트 패딩
    subtitle_wrap_width: int = 22   # 줄바꿈 너비
```

### VideoComposer

```python
class VideoComposer:
    def __init__(self, config: CompositionConfig = None):
        """영상 합성기 초기화"""

    def compose(
        self,
        audio_path: Path,
        broll_clips: List[BrollClip],
        srt_path: Optional[Path] = None,
        bgm_path: Optional[Path] = None,
        output_path: Path = None
    ) -> Path:
        """영상 합성

        1. 오디오 로드
        2. B-roll 연결
        3. 9:16 리사이즈
        4. 자막 오버레이
        5. 오디오 믹싱
        6. 렌더링
        """
```

### QuickComposer

```python
class QuickComposer:
    def __init__(self, output_dir: Path = None):
        """빠른 합성기"""

    def create_simple_video(
        self,
        audio_path: Path,
        text: str,
        background_color: Tuple[int, int, int] = (0, 0, 0),
        output_name: str = None
    ) -> Path:
        """간단한 텍스트 영상 생성"""
```

---

## MetadataGenerator

**파일**: `core/metadata_generator.py`

YouTube 업로드용 메타데이터 생성.

### MetadataGenerator

```python
class MetadataGenerator:
    def __init__(self, api_key: str = None):
        """메타데이터 생성기 초기화 (Gemini API)"""

    def generate(
        self,
        script: Dict[str, str],
        quote: Quote
    ) -> Dict[str, str]:
        """메타데이터 생성

        Returns:
            {
                "title": "영상 제목 (최대 100자)",
                "description": "영상 설명...",
                "tags": ["태그1", "태그2", ...]
            }
        """
```

---

## 사용 예시

### 전체 파이프라인

```python
from core.quote_loader import QuoteLoader
from core.script_generator import ScriptGenerator
from core.tts_engine import TTSEngine
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector
from core.video_composer import VideoComposer

# 1. 명언 로드
loader = QuoteLoader("data/quotes_library.json")
quote = loader.get_random()

# 2. 스크립트 생성
script_gen = ScriptGenerator()
script = script_gen.generate(quote)
tts_text = script_gen.generate_tts_text(script)

# 3. TTS 음성 생성
tts = TTSEngine()
audio_path = await tts.generate(tts_text, Path("output/audio.mp3"))

# 4. 자막 생성
subtitle_gen = SubtitleGenerator()
srt_path = subtitle_gen.generate_from_script(
    tts_text,
    audio_duration,
    Path("output/subtitle.srt")
)

# 5. B-roll 선택
selector = BrollSelector(assets_path=Path("assets/b-roll"))
clips = selector.select(quote.themes, audio_duration)

# 6. 영상 합성
composer = VideoComposer()
video_path = composer.compose(
    audio_path=audio_path,
    broll_clips=clips,
    srt_path=srt_path,
    output_path=Path("output/final.mp4")
)

print(f"영상 생성 완료: {video_path}")
```

---

## 환경 변수

```bash
# .env 파일
GOOGLE_API_KEY=xxx      # Gemini API (스크립트/메타데이터 생성)
PEXELS_API_KEY=xxx      # Pexels API (B-roll 검색)
```

---

## 의존성

```
# requirements.txt
google-generativeai>=0.8.0
edge-tts>=6.1.0
moviepy>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
requests>=2.31.0
```
