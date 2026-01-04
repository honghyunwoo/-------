# StoicFlow

YouTube Shorts 자동화 파이프라인 - 스토아 철학 동기부여 콘텐츠

## 설치

```bash
pip install -e .
```

## 사용법

```bash
stoicflow init              # 초기화
stoicflow scripts list      # 스크립트 목록
stoicflow record 1          # 녹음 가이드
stoicflow compose 1 --audio voice.wav  # 영상 생성
```

## 설정

`.env.example`을 `.env`로 복사하고 API 키 설정:

```bash
cp .env.example .env
```
