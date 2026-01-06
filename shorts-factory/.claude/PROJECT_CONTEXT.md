# Shorts Factory - 프로젝트 컨텍스트

> **목적**: 다음 Claude 세션에서 프로젝트 맥락을 빠르게 파악하기 위한 문서
> **마지막 업데이트**: 2026-01-06

---

## 프로젝트 개요

**Shorts Factory**는 YouTube Shorts 콘텐츠를 80% 자동화하여 생성하는 개인용 파이프라인 시스템입니다.

### 핵심 기능
- 스크립트 자동 생성 (Gemini API)
- TTS 음성 생성 (Edge-TTS)
- 자막 생성 (SRT/ASS)
- B-roll 자동 선택 (Pexels)
- 영상 합성 (FFmpeg + NVENC GPU)
- 썸네일 생성
- 업로드 메타데이터 생성

---

## 아키텍처

### 7단계 파이프라인

```
[입력: 스크립트 JSON]
       ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Script     → 6문장 구조 (V2.1 형식)                       │
│ 2. TTS        → Edge-TTS (한국어)                           │
│ 3. Subtitles  → SRT 생성 → ASS 변환                         │
│ 4. B-roll     → 테마 매칭 + 인덱스 캐싱                      │
│ 5. Compose    → FFmpeg + NVENC (23초/영상)                  │
│ 6. Thumbnail  → 훅 텍스트 오버레이                          │
│ 7. Package    → YouTube 메타데이터 생성                      │
└─────────────────────────────────────────────────────────────┘
       ↓
[출력: video.mp4, thumbnail.png, upload_info.txt]
```

### 프로젝트 구조

```
/shorts-factory/
├── /core/                      # 핵심 모듈 (13개)
│   ├── broll_selector.py       # B-roll 선택 + 인덱스 캐싱
│   ├── ffmpeg_composer.py      # FFmpeg + NVENC 합성 (메인)
│   ├── video_composer.py       # MoviePy 합성 (폴백)
│   ├── tts_engine.py           # TTS (Edge/ElevenLabs/Typecast)
│   ├── subtitle_generator.py   # 자막 생성
│   ├── script_generator.py     # 스크립트 생성 (Gemini)
│   ├── script_validator.py     # 스크립트 검증
│   ├── thumbnail_generator.py  # 썸네일 생성
│   ├── upload_packager.py      # 업로드 메타데이터
│   ├── quote_loader.py         # 명언 로드
│   ├── review_loop.py          # 재검토 루프
│   ├── metadata_generator.py   # 메타데이터 생성
│   └── gui_app.py              # GUI (선택)
│
├── /scripts/                   # 유틸리티 스크립트
│   ├── batch_generate.py       # 배치 생성 (병렬 지원)
│   ├── test_ffmpeg.py          # FFmpeg 테스트
│   ├── bulk_download_broll.py  # B-roll 다운로드
│   └── ...
│
├── /data/                      # 스크립트 데이터
│   ├── scripts_v2.1_examples.json  # V2.1 예제 (10개)
│   └── scripts_v2_samples.json     # V2 샘플
│
├── /config/                    # 설정
│   ├── settings.yaml           # 파이프라인 설정
│   ├── preset_v1.json          # FFmpeg 프리셋
│   └── .env                    # API 키 (gitignore)
│
├── /assets/                    # 에셋
│   ├── /b-roll/                # 배경 영상 (~900MB)
│   ├── /bgm/                   # 배경 음악
│   └── /fonts/                 # 폰트
│
├── /output/                    # 출력물
│   └── /YYYYMMDD_카테고리_ID/
│       ├── video.mp4
│       ├── thumbnail.png
│       ├── upload_info.txt
│       └── script.json
│
├── /docs/                      # 문서 (10개)
│   ├── 01_PRD.md ~ 06_OPERATIONS_SOP.md
│   ├── API_REFERENCE.md
│   └── CHANGELOG.md
│
└── /tests/                     # 테스트
    ├── test_quote_loader.py
    ├── test_broll_selector.py
    └── test_subtitle_generator.py
```

---

## 스크립트 V2.1 형식

### 6문장 구조

```json
{
  "id": 1,
  "version": "v2.1",
  "category": "집중_미루기",
  "topic": "2분시작",
  "mood": "dramatic",
  "cta_type": "인정형",
  "s1_hook": "왜 할 일 목록만 보면 갑자기 책상 정리가 하고 싶을까?",
  "s2_pain": "노트북 열고 1분 만에 유튜브 켠 적 있어. 나도 수십 번 했어.",
  "s3_reframe": "그건 게으름이 아니야. 뇌가 쉬운 보상부터 찾는 거야.",
  "s4_insight": "비결은 시작을 아주 작게 쪼개는 거야.",
  "s5_action": "타이머 2분, 한번 켜볼래?",
  "s6_loop_cta": "또 왔다는 건 아직 포기 안 했다는 거야.",
  "broll_keywords": ["desk", "laptop", "timer"]
}
```

### 훅 유형 (H1-H5)

| 타입 | 비율 | 패턴 | 예시 |
|-----|------|------|------|
| H1 질문형 | 20% | "왜 ~할까?" | "왜 월급날만 되면 배달앱이 켜질까?" |
| H2 충격형 | 20% | "~% 사람들이..." | "87%가 인스타 '잠깐만' 하고 한 시간을 잃어." |
| H3 공감형 | 40% | "~한 적 있지" | "노트북 켜자마자 카톡부터 확인하는 습관, 나도 그랬어." |
| H4 비밀형 | 10% | "아무도 안 알려주는..." | "아무도 안 알려주는 알림 배지가 뇌에 미치는 영향." |
| H5 대비형 | 10% | "~전과 후" | "샤워 전과 후, 피로감이 똑같다면 문제는 몸이 아니야." |

---

## 주요 명령어

### 단일 영상 생성
```bash
python scripts/batch_generate.py --id 1
```

### 배치 생성 (순차)
```bash
python scripts/batch_generate.py --all
```

### 배치 생성 (병렬 4x)
```bash
python scripts/batch_generate.py --all --parallel 4
```

### B-roll 인덱스 갱신
```bash
python main.py scan-broll
```

---

## 설정 파일 위치

| 파일 | 용도 | 경로 |
|-----|------|------|
| `.env` | API 키 | `config/.env` |
| `settings.yaml` | 파이프라인 설정 | `config/settings.yaml` |
| `preset_v1.json` | FFmpeg 프리셋 | `config/preset_v1.json` |
| `broll_index.json` | B-roll 캐시 | `assets/b-roll/broll_index.json` |

---

## 성능 지표

| 지표 | 값 |
|-----|---|
| 단일 영상 생성 | 45초 |
| 배치 20개 (순차) | 15분 |
| 배치 20개 (병렬 4x) | 4분 |
| 영상 합성 (NVENC) | 23초 |
| B-roll 로드 (캐시) | 0.1초 |

---

## 알려진 제한사항

1. **테스트 커버리지**: 25% (목표: 80%)
2. **오류 처리**: 광범위한 `except Exception` 존재
3. **Windows 전용**: NVENC 경로가 Windows 기준
