# Shorts Factory API Reference

> **핵심 모듈 API 문서**
> **버전**: 2.1.0 | **최종 업데이트**: 2026-01-06

---

## 목차

1. [QuoteLoader](#quoteloader)
2. [ScriptGenerator](#scriptgenerator)
3. [TTSEngine](#ttsengine)
4. [SubtitleGenerator](#subtitlegenerator)
5. [BrollSelector](#brollselector)
6. [VideoComposer](#videocomposer)
7. [FFmpegComposer](#ffmpegcomposer) *(NEW)*
8. [ScriptValidator](#scriptvalidator) *(NEW)*
9. [ThumbnailGenerator](#thumbnailgenerator) *(NEW)*
10. [UploadPackager](#uploadpackager) *(NEW)*
11. [MetadataGenerator](#metadatagenerator)

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

## FFmpegComposer

**파일**: `core/ffmpeg_composer.py`

FFmpeg 직접 호출 기반 고속 영상 합성 (GPU 가속).

### FFmpegComposer

```python
class FFmpegComposer:
    def __init__(self, preset: str = "default"):
        """FFmpeg 합성기 초기화

        Args:
            preset: 인코딩 프리셋 (config/preset_v1.json)
        """

    def compose(
        self,
        audio_path: Path,
        broll_clips: List[Path],
        srt_path: Optional[Path] = None,
        output_path: Path = None
    ) -> Tuple[Path, float]:
        """영상 합성 (4단계 파이프라인)

        1. B-roll concat + scale/crop (9:16)
        2. Audio merge (-shortest)
        3. Subtitles (SRT → ASS 변환)
        4. Effects (colorbalance, vignette, noise)

        Returns:
            (output_path, elapsed_seconds)
        """

def detect_encoder() -> str:
    """GPU 인코더 자동 감지

    Returns:
        'h264_nvenc' (NVIDIA) | 'h264_qsv' (Intel) |
        'h264_amf' (AMD) | 'libx264' (CPU)
    """
```

### 사용 예시

```python
from core.ffmpeg_composer import FFmpegComposer, detect_encoder

# 인코더 확인
print(detect_encoder())  # h264_nvenc

# 영상 합성
composer = FFmpegComposer()
output, elapsed = composer.compose(
    audio_path=Path("audio.mp3"),
    broll_clips=[Path("clip1.mp4"), Path("clip2.mp4")],
    srt_path=Path("subtitle.srt"),
    output_path=Path("output/video.mp4")
)
print(f"합성 완료: {elapsed:.1f}초")  # 합성 완료: 23.6초
```

---

## ScriptValidator

**파일**: `core/script_validator.py`

V2.1 스크립트 품질 검증.

### ValidationResult (Dataclass)

```python
@dataclass
class ValidationResult:
    is_valid: bool              # 검증 통과 여부
    errors: List[str]           # 에러 목록
    warnings: List[str]         # 경고 목록
    score: float                # 품질 점수 (0-100)
```

### ScriptValidator

```python
class ScriptValidator:
    # 검증 규칙
    CLICHE_PATTERNS = ["여기서 갈린다", "시작해보자", ...]
    COMMAND_PATTERNS = ["~해보자", "~하자", ...]

    def __init__(self):
        """스크립트 검증기 초기화"""

    def validate(self, script: dict) -> ValidationResult:
        """스크립트 검증

        검증 항목:
        - 필수 필드 존재 (s1_hook ~ s6_loop_cta)
        - 클리셰 사용 여부
        - 명령형 톤 비율
        - 문장별 글자 수
        - 훅 타입 다양성
        """

    def check_cliches(self, text: str) -> List[str]:
        """클리셰 패턴 검사"""

    def check_tone(self, text: str) -> float:
        """명령형 톤 비율 계산 (0.0 ~ 1.0)"""
```

### 사용 예시

```python
from core.script_validator import ScriptValidator

validator = ScriptValidator()
result = validator.validate(script_dict)

if result.is_valid:
    print(f"✅ 검증 통과 (점수: {result.score})")
else:
    for error in result.errors:
        print(f"❌ {error}")
```

---

## ThumbnailGenerator

**파일**: `core/thumbnail_generator.py`

훅 텍스트 기반 썸네일 자동 생성.

### ThumbnailConfig (Dataclass)

```python
@dataclass
class ThumbnailConfig:
    width: int = 1080           # 너비
    height: int = 1920          # 높이 (9:16)
    font_path: str = "..."      # 폰트 경로
    font_size: int = 72         # 폰트 크기
    text_color: str = "#FFFFFF" # 텍스트 색상
    bg_color: str = "#1a1a2e"   # 배경 색상
    overlay_opacity: float = 0.6 # 오버레이 투명도
```

### ThumbnailGenerator

```python
class ThumbnailGenerator:
    def __init__(self, config: ThumbnailConfig = None):
        """썸네일 생성기 초기화"""

    def generate(
        self,
        hook_text: str,
        background_image: Optional[Path] = None,
        output_path: Path = None
    ) -> Path:
        """썸네일 생성

        Args:
            hook_text: 훅 텍스트 (s1_hook)
            background_image: 배경 이미지 (없으면 그라데이션)
            output_path: 출력 경로

        Returns:
            썸네일 이미지 경로
        """

    def generate_from_video(
        self,
        video_path: Path,
        hook_text: str,
        frame_time: float = 0.5
    ) -> Path:
        """영상에서 프레임 추출 후 썸네일 생성"""
```

### 사용 예시

```python
from core.thumbnail_generator import ThumbnailGenerator

generator = ThumbnailGenerator()
thumbnail = generator.generate(
    hook_text="왜 할 일 목록만 보면\n책상 정리가 하고 싶을까?",
    output_path=Path("output/thumbnail.png")
)
```

---

## UploadPackager

**파일**: `core/upload_packager.py`

YouTube 업로드용 메타데이터 패키징.

### UploadPackage (Dataclass)

```python
@dataclass
class UploadPackage:
    video_path: Path            # 영상 경로
    thumbnail_path: Path        # 썸네일 경로
    title: str                  # 제목
    description: str            # 설명
    tags: List[str]             # 태그
    category: str               # 카테고리
    visibility: str = "private" # 공개 설정
```

### UploadPackager

```python
class UploadPackager:
    def __init__(self, output_dir: Path = None):
        """업로드 패키저 초기화"""

    def package(
        self,
        script: dict,
        video_path: Path,
        thumbnail_path: Path
    ) -> UploadPackage:
        """업로드 패키지 생성

        자동 생성 항목:
        - 제목: 훅 텍스트 기반
        - 설명: 스크립트 요약 + 해시태그
        - 태그: 카테고리 + 키워드
        """

    def export_info(
        self,
        package: UploadPackage,
        output_path: Path = None
    ) -> Path:
        """upload_info.txt 파일 생성"""

    def validate_metadata(self, package: UploadPackage) -> bool:
        """메타데이터 유효성 검사

        - 제목: 100자 이하
        - 설명: 5000자 이하
        - 태그: 500자 이하
        """
```

### 사용 예시

```python
from core.upload_packager import UploadPackager

packager = UploadPackager(output_dir=Path("output/"))
package = packager.package(
    script=script_dict,
    video_path=Path("output/video.mp4"),
    thumbnail_path=Path("output/thumbnail.png")
)

# upload_info.txt 생성
packager.export_info(package)
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
