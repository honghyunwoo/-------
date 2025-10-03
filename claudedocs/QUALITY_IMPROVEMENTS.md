# 품질 개선 가이드

Week 3 Day 20-21에서 구현된 품질 개선 사항입니다.

## 1. API 문서화 강화

### OpenAPI/Swagger 개선
**파일**: `app/asgi.py`

**추가된 기능**:
- **API 태그 설명**: 8개 카테고리별 상세 설명
  - Authentication: 사용자 인증 및 회원가입
  - Videos: AI 영상 생성 및 관리
  - Credits: 크레딧 관리 및 사용 내역
  - Payment: 결제 및 구독 관리
  - History: 영상 생성 히스토리
  - Templates: 영상 템플릿 관리
  - Teams: 팀 협업 기능
  - Health: 시스템 상태 모니터링

- **연락처 정보**:
  - 이름: 올빼미 AI 영상 스튜디오
  - URL: https://owl-studio.kr
  - 이메일: support@owl-studio.kr

- **라이선스 정보**:
  - Commercial License

**접근 URL**:
- Swagger UI: http://localhost:8080/api/docs
- ReDoc: http://localhost:8080/api/redoc
- OpenAPI JSON: http://localhost:8080/api/openapi.json

---

## 2. 통합 에러 처리 시스템

### 표준화된 에러 클래스
**파일**: `app/utils/error_handler.py`

**에러 클래스 계층**:
```
APIError (기본)
├── ValidationError (400)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
├── InsufficientCreditsError (402)
├── RateLimitError (429)
├── ServiceUnavailableError (503)
├── ExternalAPIError (502)
└── DatabaseError (500)
```

**에러 응답 형식**:
```json
{
  "message": "에러 메시지",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "email",
    "reason": "Invalid format"
  }
}
```

**사용 예제**:
```python
from app.utils.error_handler import ValidationError, NotFoundError

# 입력 검증 에러
if not email:
    raise ValidationError("이메일은 필수입니다")

# 리소스를 찾을 수 없음
user = db.query(User).filter(User.id == user_id).first()
if not user:
    raise NotFoundError("사용자", user_id)

# 크레딧 부족
if user.credits < required:
    raise InsufficientCreditsError(user.credits, required)
```

**에러 로깅**:
- 모든 에러는 자동으로 로깅됨
- 컨텍스트 정보 포함 (파일, 함수, 라인)
- 사용자 ID 포함 가능

---

## 3. 로깅 시스템 강화

### 다층 로깅 전략
**파일**: `app/config/logging.py`

**로그 파일 구조**:
```
logs/
├── app_2025-10-03.log          # 일반 로그 (일별 rotation, 30일 보관)
├── errors.log                  # 에러 전용 (100MB rotation, 10개 보관)
└── app_json_2025-10-03.log     # JSON 형식 (일별 rotation, 7일 보관)
```

**로그 레벨**:
- DEBUG: 디버깅 정보
- INFO: 일반 정보
- WARNING: 경고
- ERROR: 에러
- CRITICAL: 치명적 에러

**로그 형식**:
```
# 일반 로그
2025-10-03 14:30:45.123 | INFO     | app.services.video:generate_video:45 - Starting video generation
2025-10-03 14:30:46.789 | ERROR    | app.services.payment:process_payment:123 - Payment failed
Traceback (most recent call last):
  ...
```

```json
// JSON 로그 (분석용)
{
  "text": "Starting video generation",
  "record": {
    "time": {"repr": "2025-10-03 14:30:45.123", "timestamp": 1696337445.123},
    "level": {"name": "INFO", "no": 20},
    "message": "Starting video generation",
    "file": {"path": "./app/services/video.py", "name": "video.py"},
    "function": "generate_video",
    "line": 45
  }
}
```

**장점**:
1. **자동 Rotation**: 디스크 공간 절약
2. **자동 압축**: 오래된 로그 압축 보관
3. **에러 전용 파일**: 빠른 문제 파악
4. **JSON 형식**: 로그 분석 도구 연동 용이

---

## 4. 코드 품질 체크리스트

### 개발 시 준수사항

#### ✅ 타입 힌트
```python
# Good
def process_payment(user: User, amount: int) -> Dict[str, Any]:
    pass

# Bad
def process_payment(user, amount):
    pass
```

#### ✅ 에러 처리
```python
# Good
try:
    result = external_api.call()
except requests.RequestException as e:
    raise ExternalAPIError("Payment API", e.status_code, str(e))

# Bad
try:
    result = external_api.call()
except:
    pass
```

#### ✅ 로깅
```python
# Good
logger.info(f"User {user.id} started video generation: {task_id}")
logger.error(f"Failed to generate video for user {user.id}: {error}")

# Bad
print("Video generation started")
```

#### ✅ Docstrings
```python
# Good
def calculate_credits(plan: str, duration: int) -> int:
    """
    구독 플랜과 기간에 따른 크레딧 계산

    Args:
        plan: 구독 플랜 (free, basic, pro)
        duration: 구독 기간 (월 단위)

    Returns:
        int: 부여될 크레딧 수

    Raises:
        ValidationError: 잘못된 플랜 이름
    """
    pass

# Bad
def calculate_credits(plan, duration):
    pass
```

---

## 5. 테스트 커버리지

### 현재 테스트 현황

**테스트 파일**:
- `tests/unit/test_payment_webhook.py` (360 lines)
- `tests/unit/test_subscription_renewal.py` (325 lines)
- `tests/unit/test_rate_limiting.py` (210 lines)

**총 테스트 케이스**: 14개

**커버리지 측정** (예정):
```bash
# 설치
pip install pytest-cov

# 실행
pytest --cov=app --cov-report=html

# 결과 확인
open htmlcov/index.html
```

**목표 커버리지**:
- 전체: 70% 이상
- 핵심 서비스: 80% 이상
- API 엔드포인트: 90% 이상

---

## 6. 성능 모니터링

### 권장 사항

**1. 느린 쿼리 로깅**:
```python
# app/database/connection.py
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    if total > 1.0:  # 1초 이상
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

**2. API 응답 시간 측정**:
```python
# app/middleware/timing.py
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    if process_time > 2.0:  # 2초 이상
        logger.warning(f"Slow request ({process_time:.2f}s): {request.url}")

    return response
```

---

## 7. 보안 체크리스트

### 필수 확인 사항

- [x] Rate Limiting 적용
- [x] SQL Injection 방지 (SQLAlchemy ORM 사용)
- [x] XSS 방지 (FastAPI 자동 처리)
- [x] CSRF 방지 (토큰 기반 인증)
- [x] 민감 정보 로깅 금지
- [x] HTTPS 강제 (프로덕션)
- [x] 보안 헤더 적용

**보안 헤더** (이미 적용):
```python
# app/middleware/security.py
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Strict-Transport-Security"] = "max-age=31536000"
```

---

## 8. 배포 전 체크리스트

### 프로덕션 배포 시 확인

- [ ] 환경 변수 설정 (.env)
- [ ] 데이터베이스 마이그레이션 실행
- [ ] 로그 디렉토리 권한 확인
- [ ] Rate Limit 설정 확인
- [ ] 보안 헤더 활성화
- [ ] SSL 인증서 설정
- [ ] 크레딧 초기값 설정
- [ ] 결제 웹훅 URL 설정
- [ ] 이메일 발송 설정
- [ ] 모니터링 도구 연동

---

## 9. 지속적 개선

### 개선 사항 추적

**우선순위 P0 (긴급)**:
- [x] ERR-010: 결제 웹훅 완성
- [x] ERR-002: API 키 환경 변수화
- [x] ERR-001: DB 비밀번호 하드코딩 제거

**우선순위 P1 (중요)**:
- [x] ERR-004: 데이터베이스 마이그레이션 시스템
- [ ] ERR-008: 테스트 커버리지 확대

**우선순위 P2 (권장)**:
- [ ] 성능 최적화 (쿼리, 캐싱)
- [ ] 메트릭 수집 (Prometheus)
- [ ] APM 도구 연동 (Sentry, DataDog)

---

## 10. 참고 자료

**공식 문서**:
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Loguru: https://loguru.readthedocs.io
- Pytest: https://docs.pytest.org

**코딩 스타일**:
- PEP 8: https://peps.python.org/pep-0008/
- Type Hints: https://peps.python.org/pep-0484/

**보안**:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
