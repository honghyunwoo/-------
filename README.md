# YouTube Shorts Automation

> 스토아 철학 동기부여 채널을 위한 80% 자동화된 쇼츠 제작 시스템

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

## 프로젝트 구조

```
/
├── shorts-factory/     # 즉시 사용 가능한 쇼츠 제작 CLI
├── stoicflow/          # Clean Architecture 기반 미래 확장 베이스
├── resource/           # 공용 에셋 (폰트, 음악)
└── docs/               # 문서
```

## Shorts Factory

CLI 기반 YouTube 쇼츠 제작 파이프라인입니다.

### 빠른 시작

```bash
cd shorts-factory

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 초기 설정
python main.py setup

# 시스템 정보 확인
python main.py info
```

### 사용법

```bash
# 명언 목록 조회
python main.py list-quotes

# 스크립트 생성
python main.py generate 1 --hook H1 --cta C3

# 전체 파이프라인 실행 (스크립트 → TTS → 영상)
python main.py run 1

# 배치 처리
python main.py batch "1-5"

# 통계 확인
python main.py stats
```

### 기술 스택

- **LLM**: Claude API (스크립트 생성)
- **TTS**: TYPECAST (한국어), ElevenLabs (영어)
- **영상**: MoviePy
- **자막**: faster-whisper
- **CLI**: Click + Rich

## StoicFlow (미래 확장)

Clean Architecture 기반 차세대 파이프라인입니다.

### 예정 기능

- YouTube 자동 업로드
- 스케줄링 시스템
- 성과 분석 및 A/B 테스트
- 멀티 플랫폼 배포

자세한 아키텍처는 [STOICFLOW_ARCHITECTURE_2026.md](docs/STOICFLOW_ARCHITECTURE_2026.md) 참조

## 라이센스

MIT License
