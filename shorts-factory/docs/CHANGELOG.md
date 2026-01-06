# Shorts Factory 변경 이력

## [2.1.0] - 2026-01-06: V2.1 종합 업그레이드

### 스크립트 품질 개선

#### 클리셰 제거
- "여기서 갈린다" 100% 반복 → 10가지 고유 대안으로 교체
- 대안 예시: "바로 그 순간이야", "분기점이야", "첫걸음이 달라"

#### 톤 전환
- 명령형 비율: 55% → 40%
- 패턴 변경: "~해보자" → "~해볼래?", "~하면 어떨까"
- 제안형/질문형으로 부드러운 유도

#### 훅 다양화
| 타입 | Before | After |
|-----|--------|-------|
| H1 질문형 | 10% | 20% |
| H2 충격형 | 0% | 20% |
| H3 공감형 | 90% | 40% |
| H4 비밀형 | 0% | 10% |
| H5 대비형 | 0% | 10% |

### 파이프라인 최적화

#### 배치 병렬 처리
- `ProcessPoolExecutor` 추가 (max_workers=4)
- 사용법: `python scripts/batch_generate.py --all --parallel 4`
- 성능: 20개 배치 15분 → 4분 (4배 향상)

#### B-roll 인덱스 캐싱
- `broll_index.json` 자동 생성/갱신
- 폴더 수정 시간 기반 캐시 무효화
- 로드 시간: 1-2초 → 0.1초

### 새 모듈 추가

| 모듈 | 파일 | 기능 |
|-----|------|------|
| ScriptValidator | `core/script_validator.py` | 스크립트 품질 검증 |
| ThumbnailGenerator | `core/thumbnail_generator.py` | 썸네일 자동 생성 |
| UploadPackager | `core/upload_packager.py` | YouTube 업로드 메타데이터 |

### 문서화
- `.claude/` 폴더 생성 (세션 컨텍스트)
- `README.md` 전면 개편
- `API_REFERENCE.md` 새 모듈 추가

---

## [2.0.0] - 2026-01-06: FFmpeg 성능 최적화 (Phase B+2 완료)

### 핵심 성과
- **영상 합성 시간**: 20분 → 23.6초 (**50배 속도 향상**)
- **GPU 인코딩**: NVIDIA RTX 2080 SUPER NVENC 활용
- **품질 유지**: 기존 MoviePy와 동등한 시네마틱 효과

### 새로 추가된 파일

#### `core/ffmpeg_composer.py`
FFmpeg 직접 호출 영상 합성 모듈

**주요 기능:**
- GPU 인코더 자동 감지 (NVENC > QuickSync > AMF > CPU)
- 4단계 파이프라인:
  1. B-roll concat + scale/crop
  2. Audio merge (-shortest)
  3. Subtitles (SRT → ASS 변환)
  4. Effects (colorbalance, vignette, noise)
- VBR CQ 모드로 품질 우선 인코딩

**사용법:**
```python
from core.ffmpeg_composer import FFmpegComposer

composer = FFmpegComposer()
output_path, elapsed = composer.compose(
    audio_path=audio_path,
    broll_clips=clips,
    srt_path=srt_path,
    output_path=video_path
)
```

#### `scripts/test_ffmpeg.py`
FFmpeg Composer 테스트 스크립트

**사용법:**
```bash
python scripts/test_ffmpeg.py --id 1
```

#### `scripts/batch_generate.py`
20개 파일럿 스크립트 배치 생성

**사용법:**
```bash
python scripts/batch_generate.py --id 1      # 단일 생성
python scripts/batch_generate.py --all       # 전체 생성
```

### 기존 파일 유지 (폴백용)

#### `core/video_composer.py`
MoviePy 기반 영상 합성 (FFmpeg 실패 시 폴백)

---

## 이전 작업 (2026-01-04 ~ 2026-01-05)

### Gemini 3.0 Flash API 마이그레이션
- `core/script_generator.py`: OpenAI → Gemini API

### B-roll 시스템 개선
- `core/broll_selector.py`: fast_scan 옵션 추가
- `scripts/bulk_download_broll.py`: Pexels에서 2,500개 다운로드

### 자막 하단 위치 수정
- `core/video_composer.py`: subtitle_bottom_margin 조정

### 오디오 임시 파일 수정
- `.mp3` → `.m4a` 확장자 (Windows 호환)

---

## 시스템 사양

| 부품 | 사양 |
|------|------|
| CPU | Intel i9-9900KF (8코어 16스레드) |
| GPU | NVIDIA RTX 2080 SUPER |
| RAM | 50GB |
| FFmpeg | imageio_ffmpeg v7.1 (NVENC 지원) |

---

## 다음 단계

1. **20개 전체 영상 생성** - `batch_generate.py` 실행
2. **Phase C: B-roll 캐시** - 상위 200개 선처리
3. **Phase 3: 병렬 처리** - 대량 생산 최적화
