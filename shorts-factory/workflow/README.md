# Shorts Factory 워크플로우 가이드

> **새 Claude 세션에서 이 파일을 먼저 읽어주세요!**

## 프로젝트 개요

YouTube Shorts 자동 생성 파이프라인
- 스토아 철학/동기부여 콘텐츠
- TTS 음성 + B-roll 영상 + 자막 합성
- Pexels API로 저작권 안전한 B-roll 사용

---

## 디렉토리 구조

```
shorts-factory/
├── core/                    # 핵심 모듈
│   ├── script_generator.py  # 스크립트 생성 (Gemini API)
│   ├── tts_generator.py     # TTS 음성 생성 (Edge TTS)
│   ├── subtitle_generator.py # SRT 자막 생성
│   ├── broll_selector.py    # B-roll 선택
│   ├── broll_downloader.py  # Pexels에서 B-roll 다운로드
│   └── video_composer.py    # 최종 영상 합성
│
├── workflow/                # 워크플로우 파일
│   ├── README.md            # 이 파일
│   ├── current_project.json # 현재 작업 중인 프로젝트
│   └── templates/           # 템플릿 파일들
│
├── prompts/                 # 프롬프트 모음
│   ├── keyword_extraction.md    # 키워드 추출 프롬프트
│   └── script_generation.md     # 스크립트 생성 프롬프트
│
├── history/                 # 히스토리 (중복 방지)
│   ├── used_keywords.json   # 사용한 키워드 기록
│   └── used_broll.json      # 사용한 B-roll 기록
│
├── assets/                  # 리소스
│   ├── b-roll/              # 다운로드된 B-roll 영상
│   └── bgm/                 # 배경 음악
│
└── output/                  # 생성된 영상
    └── YYYY-MM-DD_quote_N/  # 날짜별 출력
```

---

## 영상 생성 워크플로우

### 단계 1: 스크립트 준비

사용자가 스크립트를 제공하거나, Gemini API로 생성:

```bash
python -c "from core.script_generator import ScriptGenerator; ..."
```

또는 `workflow/current_project.json`에 직접 작성

### 단계 2: 키워드 생성 (Claude 필요)

**중요**: 이 단계는 Claude와 대화하며 진행

1. `workflow/current_project.json`의 스크립트 확인
2. `prompts/keyword_extraction.md` 프롬프트 참고
3. `history/used_keywords.json` 중복 체크
4. 새 키워드를 `workflow/current_project.json`에 추가

### 단계 3: B-roll 다운로드

키워드로 Pexels에서 B-roll 검색 및 다운로드:

```bash
python scripts/download_broll_by_keywords.py
```

### 단계 4: 영상 생성

모든 준비가 완료되면:

```bash
python generate_video.py
```

---

## 현재 프로젝트 파일 형식

`workflow/current_project.json`:

```json
{
  "project_id": "2026-01-05_quote_1",
  "theme": "stoic",
  "script": {
    "hook": "왜 2000년 전 로마 황제의 일기장이...",
    "quote": "운명이 가져다주는 것을...",
    "explanation": "이것은 체념이 아니라...",
    "application": "오늘 당신이 겪은...",
    "cta": "이 영상이 도움이 됐다면..."
  },
  "tts_text": "전체 나레이션 텍스트...",
  "keywords": [
    {"time": "0:00-0:05", "text": "왜 2000년 전...", "keywords": ["ancient", "rome", "journal"]},
    {"time": "0:05-0:15", "text": "운명이 가져다주는...", "keywords": ["fate", "destiny", "embrace"]}
  ],
  "style": {
    "color_tone": "dark_moody",
    "subtitle_highlight": true,
    "bgm": "ambient"
  }
}
```

---

## 중요 설정

### API 키 (.env)
```
GOOGLE_API_KEY=xxx      # Gemini API (스크립트 생성)
PEXELS_API_KEY=xxx      # Pexels API (B-roll 검색)
```

### 자막 설정 (video_composer.py)
- 폰트: Malgun Gothic (48px)
- 위치: 하단 고정 (1600px)
- margin=(0, 20) 으로 stroke 짤림 방지

---

## 자주 사용하는 명령어

```bash
# 전체 파이프라인 실행
python main.py --theme stoic --style cinematic

# 특정 스크립트로 영상 생성
python generate_best_video.py

# B-roll만 다운로드
python scripts/download_broll.py --keywords "storm,statue,ocean"

# 테스트 영상 생성 (빠른 확인용)
python generate_srt_test.py
```

---

## 문제 해결

### 자막이 짤리는 경우
- `video_composer.py`의 `margin=(0, 20)` 확인
- `desired_bottom = 1600` 값 조정

### B-roll 품질이 낮은 경우
- Pexels에서 HD/4K 필터 적용
- `broll_downloader.py`에서 `min_duration`, `min_width` 조정

### 영상이 재생 안 되는 경우
- 생성 중 중단되면 파일 손상
- 다시 생성 필요

---

## 다음 개선 예정

- [x] 키워드 기반 B-roll 자동 매칭 (아래 상세 계획 참조)
- [ ] Word-by-word 자막 하이라이트
- [ ] LUT 색보정 적용
- [ ] 자막 애니메이션 효과

---

## B-roll 자동 매칭 워크플로우

### 개요

스크립트 섹션별로 키워드를 추출하고, 해당 키워드에 맞는 B-roll을 자동 매칭하는 시스템.

### 1단계: 스크립트 분석 및 키워드 추출

```
스크립트 → AI 분석 → 시간대별 키워드 매핑
```

| 시간대 | 섹션 | 추출 키워드 | B-roll 스타일 |
|--------|------|-------------|---------------|
| 0:00-0:03 | 훅 | curiosity, ancient, journal | 빠른 줌, 드라마틱 |
| 0:03-0:08 | 명언 | stoic, statue, marble | Ken Burns 느린 줌 |
| 0:08-0:20 | 해설 | nature, calm, meditation | 부드러운 전환 |
| 0:20-0:28 | 적용 | modern, city, walking | 실생활 장면 |
| 0:28-0:32 | CTA | sunrise, hope, growth | 긍정적 이미지 |

### 2단계: B-roll 검색 및 다운로드

```python
# 키워드로 Pexels API 검색
keywords = ["stoic", "statue", "marble"]
results = broll_downloader.search_pexels(keywords, orientation="portrait")

# 세로 영상(9:16) 필터링
vertical_clips = [r for r in results if r["aspect_ratio"] < 1]
```

**검색 우선순위:**
1. 세로 영상 (portrait) 우선
2. HD/4K 해상도
3. 5-15초 길이
4. 인물 없는 추상적 영상 (저작권 안전)

### 3단계: 테마 기반 자동 매칭

`broll_selector.py`의 `THEME_KEYWORDS` 활용:

```python
THEME_KEYWORDS = {
    "역경": ["mountain", "storm", "rain", "struggle", "climbing"],
    "마음": ["meditation", "peace", "calm", "nature", "water"],
    "시간": ["clock", "hourglass", "sunset", "sunrise", "time-lapse"],
    "통제": ["control", "focus", "discipline", "routine"],
    "죽음": ["autumn", "leaves", "cycle", "ending", "memorial"],
    "미덕": ["light", "growth", "garden", "wisdom"],
    "행복": ["joy", "smile", "celebration", "sunshine"],
    "자연": ["nature", "forest", "ocean", "sky", "landscape"],
    "도시": ["city", "urban", "building", "street"],
    "추상": ["abstract", "particles", "geometric", "motion"]
}
```

### 4단계: 매칭 알고리즘

```
┌─────────────────────────────────────────────────────────────┐
│                    B-roll 매칭 플로우                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 스크립트 섹션별 키워드 추출                              │
│     └── Gemini API로 키워드 생성                            │
│                                                             │
│  2. 로컬 B-roll 검색                                        │
│     ├── assets/b-roll/ 폴더 스캔                            │
│     ├── 파일명/폴더명으로 테마 추출                          │
│     └── 키워드 매칭 점수 계산                               │
│                                                             │
│  3. 매칭 점수 계산                                          │
│     ├── 직접 키워드 매칭: +10점                             │
│     ├── 테마 키워드 매칭: +5점                              │
│     └── 폴더명 매칭: +3점                                   │
│                                                             │
│  4. 최적 클립 선택                                          │
│     ├── 점수 높은 순으로 정렬                               │
│     ├── 중복 방지 (같은 클립 재사용 방지)                    │
│     └── 길이에 맞게 자르기/반복                             │
│                                                             │
│  5. 부족 시 Pexels API 검색                                 │
│     └── 새 B-roll 다운로드 → assets/b-roll/에 저장          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5단계: 자동화 스크립트

```bash
# 전체 자동화 파이프라인
python main.py --quote-id 1 --auto-broll

# 개별 단계 실행
python scripts/extract_keywords.py --script "스크립트 텍스트"
python scripts/match_broll.py --keywords "stoic,statue" --duration 30
python scripts/download_missing_broll.py
```

### 매칭 품질 체크리스트

- [ ] 각 섹션에 맞는 분위기의 B-roll 사용
- [ ] 같은 클립 연속 사용 방지 (최소 3개 다른 클립)
- [ ] 세로 영상(9:16) 비율 확인
- [ ] 화질 HD 이상 확인
- [ ] 워터마크 없는 영상 확인

### 폴백 전략

1. **매칭 실패 시**: 기본 테마(자연/추상) B-roll 사용
2. **로컬 부족 시**: Pexels API 실시간 검색
3. **API 실패 시**: 검은 배경 + 텍스트 카드

---
