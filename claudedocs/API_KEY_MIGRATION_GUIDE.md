# 🔐 API 키 마이그레이션 가이드

**작성자**: Claude (수석 개발자)
**작성일**: 2025-10-03
**목적**: config.toml → .env 마이그레이션 (보안 강화)

---

## 🚨 긴급 조치 사항

### 현재 문제
`config.toml` 파일에 실제 API 키가 하드코딩되어 있습니다. 이것은 **CRITICAL 보안 위협**입니다.

### 즉시 조치
1. 현재 `config.toml`에서 API 키를 `.env` 파일로 이동
2. `config.toml`의 모든 API 키를 빈 문자열로 변경
3. `.env` 파일에서만 실제 키 관리

---

## 📋 마이그레이션 절차

### Step 1: 현재 API 키 확인

`config.toml` 파일을 열고 다음 값들을 확인하세요:

```toml
[app]
pexels_api_keys = [ "84S18I3DIXma1iV3xyT6uIQb9fxSzH6h77NhiLxNYZtTHRCu1Il6Auwb",]
openai_api_key = ""
azure_api_key = ""
gemini_api_key = ""
# ... 등등
```

### Step 2: .env 파일 생성

루트 디렉토리에 `.env` 파일을 만듭니다:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Step 3: API 키 복사

`config.toml`에서 찾은 API 키를 `.env` 파일에 추가합니다:

```bash
# .env 파일 예시

# Pexels API 키 (config.toml에서 복사)
PEXELS_API_KEY=84S18I3DIXma1iV3xyT6uIQb9fxSzH6h77NhiLxNYZtTHRCu1Il6Auwb

# OpenAI API 키 (있다면)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Azure API 키 (있다면)
AZURE_API_KEY=your-azure-key-here

# YouTube API 키 (있다면)
YOUTUBE_API_KEY=your-youtube-key-here
```

### Step 4: config.toml 정리

`config.toml`의 모든 API 키를 **빈 문자열** 또는 **빈 배열**로 변경합니다:

```toml
[app]
pexels_api_keys = []  # 빈 배열
pixabay_api_keys = []
openai_api_key = ""  # 빈 문자열
azure_api_key = ""
gemini_api_key = ""
```

### Step 5: 테스트

애플리케이션을 실행하여 `.env` 파일의 API 키가 올바르게 로드되는지 확인합니다:

```bash
python app/main.py
```

로그에 다음과 같은 메시지가 표시되어야 합니다:

```
✓ Using PEXELS_API_KEY from environment variable
✓ Using OPENAI_API_KEY from environment variable
```

---

## 🔄 작동 원리

### 우선순위 시스템

`app/config/config.py`는 다음 우선순위로 설정을 로드합니다:

1. **환경 변수** (.env 파일) - **최우선**
2. config.toml 파일
3. config.example.toml (기본값)

### 코드 예시

```python
# app/config/config.py

def apply_env_overrides(config):
    """
    환경 변수로 민감한 설정을 오버라이드합니다.
    .env 파일의 값이 config.toml보다 우선순위가 높습니다.
    """
    app = config.get("app", {})

    # .env의 PEXELS_API_KEY가 있으면 config.toml 값을 덮어씁니다
    if os.getenv("PEXELS_API_KEY"):
        app["pexels_api_keys"] = [os.getenv("PEXELS_API_KEY")]
        logger.info("✓ Using PEXELS_API_KEY from environment variable")

    # ... 다른 키들도 동일하게 처리
```

---

## 🛡️ 보안 체크리스트

### 마이그레이션 완료 후 확인

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있음
- [ ] `config.toml`에 실제 API 키가 없음 (모두 빈 값)
- [ ] `.env` 파일에 실제 API 키가 있음
- [ ] 애플리케이션이 정상 작동함
- [ ] 로그에 "Using XXX from environment variable" 메시지 표시됨

### Git 상태 확인

```bash
# .env 파일이 무시되는지 확인
git check-ignore .env
# 출력: .gitignore:17:.env	.env

# config.toml이 변경되었는지 확인
git status
# 출력: modified:   config.toml (API 키 제거됨)
```

---

## 📝 지원되는 환경 변수

### 영상 소스 API
- `PEXELS_API_KEY` - Pexels 무료 영상
- `PIXABAY_API_KEY` - Pixabay 무료 영상

### AI 모델 API
- `OPENAI_API_KEY` - OpenAI ChatGPT
- `AZURE_API_KEY` - Azure OpenAI
- `GEMINI_API_KEY` - Google Gemini

### 음성 합성 API
- `AZURE_SPEECH_KEY` - Azure TTS
- `AZURE_SPEECH_REGION` - Azure TTS 리전

### 기타 API
- `YOUTUBE_API_KEY` - YouTube Data API v3
- `JWT_SECRET_KEY` - JWT 인증 시크릿

전체 목록은 `.env.example` 파일을 참조하세요.

---

## ⚠️ 주의사항

### 절대 하지 말아야 할 것
1. ❌ `.env` 파일을 Git에 커밋하지 마세요
2. ❌ `config.toml`에 실제 API 키를 다시 입력하지 마세요
3. ❌ API 키를 Slack, 이메일, 메신저로 공유하지 마세요
4. ❌ `.env` 파일을 공개 저장소에 업로드하지 마세요

### 팀 협업 시
- `.env.example` 파일만 Git에 커밋하세요
- 각 팀원이 자신의 `.env` 파일을 생성하도록 안내하세요
- 실제 API 키는 안전한 방법으로 공유하세요 (1Password, LastPass 등)

### 프로덕션 배포 시
- 서버 환경 변수에 직접 설정하세요
- AWS Secrets Manager, Azure Key Vault 등 사용을 권장합니다
- `.env` 파일을 서버에 복사하지 마세요 (환경 변수 직접 설정)

---

## 🆘 문제 해결

### 문제 1: "API key not found" 오류

**원인**: `.env` 파일이 로드되지 않음

**해결**:
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `python-dotenv` 패키지 설치 확인: `pip install python-dotenv`
3. 애플리케이션 재시작

### 문제 2: "Invalid API key" 오류

**원인**: `.env` 파일의 API 키가 잘못됨

**해결**:
1. `.env` 파일을 열고 API 키 확인
2. 공백, 따옴표가 없는지 확인 (올바른 형식: `PEXELS_API_KEY=abc123`)
3. API 키 재발급 후 다시 입력

### 문제 3: "Using config.toml values" 메시지

**원인**: `.env` 파일의 값이 비어 있음

**해결**:
1. `.env` 파일에 실제 API 키를 입력했는지 확인
2. 키 이름이 정확한지 확인 (대소문자 구분)
3. 애플리케이션 재시작

---

## 📚 관련 문서
- [ERROR_TRACKING.md](./ERROR_TRACKING.md) - ERR-002: API 키 노출 위험
- [SECURITY_PATCH_2025-10-03.md](./SECURITY_PATCH_2025-10-03.md) - 보안 패치 기록
- [PROJECT_MASTER_PLAN.md](./PROJECT_MASTER_PLAN.md) - Week 1 보안 강화 계획

---

**마지막 업데이트**: 2025-10-03
**다음 리뷰**: 2025-10-04

🦉 **올빼미 AI 영상 스튜디오** - 안전한 API 키 관리로 보안 강화!
