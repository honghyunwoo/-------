# 🦉 올빼미 AI 영상 스튜디오

> AI가 24시간 함께 만드는 프리미엄 영상 제작 서비스

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)

## 🌟 주요 특징

### 📈 상용화 완료
- ✅ **사용자 인증 시스템** (JWT 기반 회원가입/로그인)
- ✅ **크레딧 시스템** (무료 3개, 유료 플랜별 차등)
- ✅ **결제 연동** (토스페이먼츠 API)
- ✅ **사용량 제한** (플랜별 영상 생성 제한)

### 🎯 핵심 기능
- 🤖 **AI 자동 대본 생성** - 키워드만 입력하면 완벽한 영상 스크립트 생성
- 🎬 **자동 영상 제작** - 스크립트 기반 자동 영상 소스 매칭
- 🎵 **프리미엄 음성 합성** - 한국어 최적화 자연스러운 TTS
- 📝 **자막 자동 생성** - 영상에 맞는 자막 자동 삽입
- 🎨 **한국형 템플릿** - 맛집, 쇼핑몰, 교육, 부동산용 템플릿

## 💰 요금제

| 플랜 | 무료 | 베이직 | 프로 | 비즈니스 |
|------|------|---------|------|----------|
| 월 영상 개수 | 3개 | 20개 | 100개 | 무제한 |
| 월 요금 | 0원 | 29,000원 | 99,000원 | 299,000원 |
| 고급 템플릿 | ❌ | ✅ | ✅ | ✅ |
| 워터마크 제거 | ❌ | ❌ | ✅ | ✅ |
| API 액세스 | ❌ | ❌ | ❌ | ✅ |
| 전용 지원 | ❌ | ❌ | ❌ | ✅ |

## 🚀 빠른 시작

### 1. 필수 요구사항
- Python 3.10 이상
- PostgreSQL 13 이상
- FFmpeg
- ImageMagick

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/owl-studio/moneyprinter-owl.git
cd moneyprinter-owl

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# 데이터베이스 설정
DATABASE_URL=postgresql://owl_user:your_password@localhost/owl_studio

# JWT 인증 설정
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 토스페이먼츠 설정
TOSS_CLIENT_KEY=your_client_key
TOSS_SECRET_KEY=your_secret_key

# OpenAI (선택사항)
OPENAI_API_KEY=your_openai_key
```

### 4. 데이터베이스 초기화

```bash
# PostgreSQL 데이터베이스 생성
createdb owl_studio

# 테이블 생성 (앱 실행 시 자동 생성)
python main.py --init-db
```

### 5. 실행

#### Windows
```bash
webui.bat
```

#### Linux/Mac
```bash
./webui.sh
```

브라우저에서 `http://localhost:8501` 접속

## 🐳 Docker 사용

```bash
# 이미지 빌드
docker build -t owl-studio .

# 컨테이너 실행
docker-compose up -d
```

## 📖 사용 방법

### 1. 회원가입 및 로그인
1. 웹 인터페이스에서 회원가입
2. 이메일과 비밀번호로 로그인
3. 무료 크레딧 3개로 시작

### 2. 영상 생성
1. **영상 주제 입력** - 원하는 키워드나 주제 입력
2. **AI 대본 생성** - AI가 자동으로 스크립트 생성
3. **설정 조정** - 음성, 배경음악, 자막 스타일 등 설정
4. **영상 생성** - 생성 버튼 클릭 (약 3분 소요)
5. **다운로드** - 완성된 영상 다운로드

### 3. 업그레이드
- 더 많은 영상이 필요하면 유료 플랜으로 업그레이드
- 결제 페이지에서 원하는 플랜 선택
- 토스페이먼츠로 안전하게 결제

## 🔧 고급 설정

### API 사용

```python
import requests

# 인증
response = requests.post("http://localhost:8080/auth/token",
    data={"username": "user@example.com", "password": "password"})
token = response.json()["access_token"]

# 영상 생성
headers = {"Authorization": f"Bearer {token}"}
params = {
    "video_subject": "맛있는 김치찌개 레시피",
    "video_language": "ko",
    "voice_name": "ko-KR-SunHiNeural"
}
response = requests.post("http://localhost:8080/api/v1/videos",
    json=params, headers=headers)
```

### 커스텀 템플릿

```python
# app/templates/custom.json
{
    "name": "우리 브랜드 템플릿",
    "category": "brand",
    "parameters": {
        "font_name": "NanumGothic",
        "text_color": "#FF5733",
        "bgm_type": "corporate"
    }
}
```

## 📊 성능

- ⚡ **영상 생성 속도**: 3분 이내 (1분 영상 기준)
- 🔄 **동시 처리**: 최대 5개 영상 동시 생성
- 💾 **캐싱**: Redis 캐싱으로 반복 작업 50% 단축
- 📈 **확장성**: 수평 확장 지원 (Docker Swarm/K8s)

## 🤝 기여하기

프로젝트 개선에 참여하고 싶으시다면:

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📝 라이센스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🙋 자주 묻는 질문

**Q: 무료 플랜으로 어떤 영상을 만들 수 있나요?**
A: 월 3개까지 최대 1분 길이의 영상을 생성할 수 있습니다.

**Q: 영상 저작권은 누구에게 있나요?**
A: 생성된 영상의 저작권은 100% 사용자에게 있습니다.

**Q: 한국어 외 다른 언어도 지원하나요?**
A: 현재 한국어, 영어, 중국어, 일본어를 지원합니다.

## 📞 문의

- 📧 이메일: support@owl-studio.kr
- 💬 디스코드: https://discord.gg/owl-studio
- 🌐 웹사이트: https://owl-studio.kr

---

<p align="center">
  Made with ❤️ by 올빼미 스튜디오
  <br>
  밤새우며 만드는 완벽한 영상
</p>