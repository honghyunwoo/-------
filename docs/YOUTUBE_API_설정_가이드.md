# YouTube Data API v3 연동 가이드

올빼미 AI 영상 스튜디오에서 YouTube 트렌드 분석 기능을 사용하려면 YouTube Data API v3 키가 필요합니다.

## 📌 API 키 발급 방법

### 1. Google Cloud Console 접속
https://console.cloud.google.com/

### 2. 프로젝트 생성 또는 선택
- 좌측 상단의 프로젝트 선택 드롭다운 클릭
- 새 프로젝트 생성 또는 기존 프로젝트 선택

### 3. YouTube Data API v3 활성화
1. 좌측 메뉴에서 **API 및 서비스** → **라이브러리** 클릭
2. 검색창에 `YouTube Data API v3` 검색
3. **YouTube Data API v3** 선택
4. **사용** 버튼 클릭

### 4. API 키 생성
1. 좌측 메뉴에서 **API 및 서비스** → **사용자 인증 정보** 클릭
2. 상단의 **+ 사용자 인증 정보 만들기** 클릭
3. **API 키** 선택
4. 생성된 API 키 복사

### 5. API 키 제한 설정 (권장)
1. 생성된 API 키 옆의 **편집** (연필 아이콘) 클릭
2. **API 제한사항** 섹션에서:
   - **API 제한** 선택
   - **YouTube Data API v3** 체크
3. **저장** 버튼 클릭

## ⚙️ config.toml 설정

프로젝트 루트의 `config.toml` 파일에 발급받은 API 키를 입력하세요:

```toml
[youtube]
# YouTube Data API v3 키 설정
# https://console.cloud.google.com/apis/credentials 에서 발급
api_key = "여기에_발급받은_API_키_입력"
```

## ✅ 설정 확인

API 키 설정 후 트렌드 분석이 정상 작동하는지 확인:

```bash
cd "C:/Users/hynoo/OneDrive/바탕 화면/올빼미/MoneyPrinterTurbo"
python -c "
from app.services.youtube_trend import YouTubeTrendAnalyzer
analyzer = YouTubeTrendAnalyzer()
result = analyzer.generate_content_suggestions('AI 영상 제작')
print('✅ API 연동 성공!' if result else '❌ API 키를 확인하세요')
"
```

## 📊 API 할당량

YouTube Data API v3는 일일 무료 할당량이 있습니다:
- **일일 할당량**: 10,000 units
- **트렌드 조회**: 약 1 unit
- **영상 정보 조회**: 약 1 unit

**예상 사용량**:
- 트렌드 분석 1회: 약 100 units (50개 영상 조회)
- 하루 약 100회 분석 가능

## 🔒 API 키 보안

**주의사항**:
- API 키를 GitHub에 커밋하지 마세요
- `.gitignore`에 `config.toml`이 포함되어 있는지 확인하세요
- 공개 저장소에 업로드하지 마세요

## 🚨 Fallback 모드

API 키가 없어도 기본 기능은 작동합니다:
- 미리 정의된 바이럴 키워드 사용
- 표준 제목 패턴 적용
- 기본 콘텐츠 훅 제공

**차이점**:
- ❌ 실시간 트렌드 데이터 없음
- ❌ 실제 인기 영상 분석 불가
- ✅ 기본 SEO 최적화는 정상 작동

## 📞 문의

API 설정 관련 문의:
- GitHub Issues: [프로젝트 저장소]
- Email: [이메일 주소]
