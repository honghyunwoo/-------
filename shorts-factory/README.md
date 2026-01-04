# Shorts Factory 🎬

유튜브 쇼츠 콘텐츠를 80% 자동화하여 생성하는 개인용 파이프라인 시스템.

## 📋 프로젝트 개요

- **채널 1**: 스토아 철학 동기부여 (매일 스토아)
- **채널 2**: 영어학습 (준비 중)
- **목표**: 영상 1개당 10분 이내 제작
- **자동화**: 스크립트 생성 → TTS → 영상 합성

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 초기 설정 (폴더 구조 생성)
python main.py setup

# 환경 변수 설정
# config/.env 파일에 API 키 입력
```

### 2. 기본 사용법

```bash
# 시스템 정보 확인
python main.py info

# 명언 목록 조회
python main.py list-quotes

# 미사용 명언 조회
python main.py list-unused --limit 5

# 스크립트만 생성
python main.py generate 1 --hook H1 --cta C3

# 전체 파이프라인 실행 (스크립트 → TTS → 영상)
python main.py run 1

# TTS/영상 없이 스크립트만
python main.py run 1 --skip-tts

# 배치 처리 (여러 명언 한 번에)
python main.py batch "1-5"
python main.py batch "1,3,5,7"

# B-roll 인덱스 갱신
python main.py scan-broll

# 통계 확인
python main.py stats
```

## 📁 프로젝트 구조

```
/shorts-factory/
├── main.py                 # CLI 진입점
├── pipeline.py             # 파이프라인 오케스트레이터
├── requirements.txt        # 의존성
├── /core/                  # 핵심 모듈
│   ├── quote_loader.py     # 명언 로드
│   ├── script_generator.py # 스크립트 생성
│   ├── review_loop.py      # 재검토 루프
│   ├── tts_engine.py       # TTS 엔진 (TYPECAST/ElevenLabs)
│   ├── subtitle_generator.py # 자막 생성
│   ├── broll_selector.py   # B-roll 선택
│   ├── video_composer.py   # 영상 합성
│   └── metadata_generator.py # 메타데이터 생성
├── /templates/             # 콘텐츠 템플릿
│   └── /stoic/
│       ├── quotes_library.json
│       ├── prompts.yaml
│       └── *.json
├── /assets/                # 에셋
│   ├── /b-roll/            # 배경 영상
│   │   ├── /nature/
│   │   ├── /city/
│   │   └── /abstract/
│   ├── /bgm/               # 배경 음악
│   └── /fonts/             # 폰트
├── /config/                # 설정
│   ├── settings.yaml
│   └── .env
├── /output/                # 출력물
└── /docs/                  # 문서
    ├── 01_PRD.md
    ├── 02_MVP.md
    ├── 03_5W1H.md
    ├── 04_TECHNICAL_DESIGN.md
    ├── 05_CONTENT_GUIDELINE.md
    └── 06_OPERATIONS_SOP.md
```

## 🛠️ 기술 스택

- **언어**: Python 3.11+
- **LLM**: Claude API (스크립트 생성, 재검토)
- **TTS**: TYPECAST (한국어), ElevenLabs (영어)
- **영상**: MoviePy
- **자막**: faster-whisper (음성 인식)
- **CLI**: Click + Rich

## 📖 문서

- [PRD (제품 요구사항)](docs/01_PRD.md)
- [MVP 정의서](docs/02_MVP.md)
- [5W1H](docs/03_5W1H.md)
- [기술 설계서](docs/04_TECHNICAL_DESIGN.md)
- [콘텐츠 가이드라인](docs/05_CONTENT_GUIDELINE.md)
- [운영 SOP](docs/06_OPERATIONS_SOP.md)

## 🎯 훅 유형

| 코드 | 유형 | 설명 |
|-----|-----|-----|
| H1 | 질문형 | 시청자에게 직접 질문 |
| H2 | 충격형 | 놀라운 사실로 시선 끌기 |
| H3 | 공감형 | 시청자의 감정에 공감 |
| H4 | 비밀형 | 숨겨진 지혜 공개 |
| H5 | 대비형 | 대조를 통한 흥미 유발 |

## 🎬 CTA 유형

| 코드 | 유형 | 설명 |
|-----|-----|-----|
| C1 | 저장 유도 | 영상 저장 유도 |
| C2 | 팔로우 유도 | 채널 구독 유도 |
| C3 | 오픈 엔딩 | 질문으로 재시청 유도 |
| C4 | 공유 유도 | 영상 공유 유도 |
| C5 | 시리즈 예고 | 다음 영상 예고 |

## 📅 로드맵

- [x] Phase 0: 문서화 및 설계
- [x] Phase 1: 핵심 모듈 구현 (스크립트 생성)
- [x] Phase 2: TTS 연동
- [x] Phase 3: 영상 합성
- [ ] Phase 4: 채널 런칭

## 💰 예상 비용

| 항목 | 월 비용 |
|-----|--------|
| Claude API | ~$5 |
| TYPECAST | ~₩20,000 |
| ElevenLabs | ~$5 |
| **총합** | **~₩35,000/월** |

---

Made with ❤️ by Shorts Factory
