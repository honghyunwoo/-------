# 🧪 올빼미 AI 영상 스튜디오 - 테스트 가이드

**작성일**: 2025-10-03
**버전**: 1.0
**대상**: Week 6 Day 36-39

---

## 📋 목차

1. [테스트 전략](#테스트-전략)
2. [테스트 환경 설정](#테스트-환경-설정)
3. [단위 테스트](#단위-테스트)
4. [통합 테스트](#통합-테스트)
5. [E2E 테스트](#e2e-테스트)
6. [성능 테스트](#성능-테스트)
7. [보안 테스트](#보안-테스트)
8. [베타 테스트](#베타-테스트)
9. [테스트 자동화](#테스트-자동화)

---

## 테스트 전략

### 🎯 테스트 피라미드

```
        ┌───────────┐
        │    E2E    │  소수 (5%)
        │   Tests   │
        ├───────────┤
        │Integration│  중간 (15%)
        │   Tests   │
        ├───────────┤
        │   Unit    │  다수 (80%)
        │   Tests   │
        └───────────┘
```

### 📊 테스트 커버리지 목표

| 레이어 | 목표 커버리지 | 현재 상태 |
|--------|--------------|----------|
| **Unit Tests** | 80% | 작성 필요 |
| **Integration Tests** | 60% | 일부 작성 |
| **E2E Tests** | 주요 흐름 100% | 작성 완료 |

---

## 테스트 환경 설정

### 1. 테스트 의존성 설치

```bash
# 테스트 라이브러리 설치
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx faker

# requirements-test.txt 생성
cat > requirements-test.txt << EOF
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
pytest-mock==3.12.0
httpx==0.25.2
faker==20.1.0
locust==2.19.0
EOF

pip install -r requirements-test.txt
```

### 2. 테스트 설정 파일

**pytest.ini**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=app
    --cov-report=html
    --cov-report=term
    --cov-fail-under=70
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    security: Security tests
    performance: Performance tests
```

### 3. 테스트 환경 변수

**.env.test**:
```bash
APP_ENV=testing
USE_SQLITE=true
JWT_SECRET_KEY=test-secret-key-for-testing
OPENAI_API_KEY=test-key
PEXELS_API_KEY=test-key
SENTRY_DSN=
```

---

## 단위 테스트

### 예시: 사용자 인증 테스트

**tests/unit/test_auth.py**:
```python
import pytest
from app.services import auth
from app.models.user import User

@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }

def test_hash_password():
    """비밀번호 해싱 테스트"""
    password = "MySecurePassword123!"
    hashed = auth.hash_password(password)

    assert hashed != password
    assert auth.verify_password(password, hashed)

def test_verify_password_invalid():
    """잘못된 비밀번호 검증"""
    password = "CorrectPassword"
    hashed = auth.hash_password(password)

    assert not auth.verify_password("WrongPassword", hashed)

def test_create_jwt_token():
    """JWT 토큰 생성 테스트"""
    user_id = 123
    token = auth.create_access_token(data={"user_id": user_id})

    assert token is not None
    assert isinstance(token, str)
```

### 실행 방법

```bash
# 모든 단위 테스트 실행
pytest tests/unit/ -v

# 특정 파일 실행
pytest tests/unit/test_auth.py -v

# 커버리지 포함
pytest tests/unit/ --cov=app --cov-report=html
```

---

## 통합 테스트

### 예시: API 엔드포인트 테스트

**tests/integration/test_api.py**:
```python
import pytest
from fastapi.testclient import TestClient
from app.asgi import app

client = TestClient(app)

def test_register_and_login():
    """회원가입 후 로그인 통합 테스트"""
    # 회원가입
    register_data = {
        "username": "integrationuser",
        "email": "integration@test.com",
        "password": "TestPass123!"
    }

    response = client.post("/auth/register", json=register_data)
    assert response.status_code == 200

    # 로그인
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data["data"]

def test_protected_endpoint_without_token():
    """인증 없이 보호된 엔드포인트 접근"""
    response = client.get("/credits/balance")
    assert response.status_code == 401
```

---

## E2E 테스트

### 전체 워크플로우 테스트

이미 작성된 `tests/e2e/test_full_workflow.py` 사용

### 실행 방법

```bash
# E2E 테스트 실행
pytest tests/e2e/ -v -s

# 특정 테스트 클래스만 실행
pytest tests/e2e/test_full_workflow.py::TestFullWorkflow -v
```

### 주요 시나리오

1. ✅ 사용자 회원가입
2. ✅ 사용자 로그인
3. ✅ 크레딧 잔액 확인
4. ✅ 영상 생성 요청
5. ✅ 구독 플랜 조회
6. ✅ 결제 요청
7. ✅ 히스토리 조회
8. ✅ 헬스 체크

---

## 성능 테스트

### Locust를 사용한 부하 테스트

**locustfile.py**:
```python
from locust import HttpUser, task, between

class OwlStudioUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """각 사용자 시작 시 로그인"""
        response = self.client.post("/auth/login", json={
            "email": "loadtest@example.com",
            "password": "LoadTest123!"
        })

        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
        else:
            self.token = None

    @task(3)
    def view_dashboard(self):
        """대시보드 조회 (빈도 높음)"""
        if self.token:
            self.client.get(
                "/api/monitoring/dashboard",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def check_credits(self):
        """크레딧 잔액 확인"""
        if self.token:
            self.client.get(
                "/credits/balance",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def view_history(self):
        """히스토리 조회 (빈도 낮음)"""
        if self.token:
            self.client.get(
                "/history",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(5)
    def health_check(self):
        """헬스 체크 (빈도 높음)"""
        self.client.get("/health")
```

### 부하 테스트 실행

```bash
# Locust 서버 시작
locust -f locustfile.py --host=http://localhost:8080

# 웹 UI 접속: http://localhost:8089

# CLI로 실행 (100명 사용자, 초당 10명씩 증가)
locust -f locustfile.py \
  --host=http://localhost:8080 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless
```

### 성능 목표

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| **응답 시간 (P95)** | < 500ms | Locust, Prometheus |
| **처리량** | > 100 req/s | Locust |
| **에러율** | < 1% | Sentry, Locust |
| **동시 사용자** | 100명 | Locust |

---

## 보안 테스트

### OWASP Top 10 체크리스트

#### 1. SQL Injection

```bash
# 테스트
pytest tests/e2e/test_full_workflow.py::TestSecurityFeatures::test_sql_injection_prevention -v
```

#### 2. XSS (Cross-Site Scripting)

```python
def test_xss_prevention():
    """XSS 공격 방어 테스트"""
    malicious_input = "<script>alert('XSS')</script>"

    response = client.post("/auth/register", json={
        "username": malicious_input,
        "email": "xss@test.com",
        "password": "Test123!"
    })

    # 입력이 이스케이프되어야 함
    assert response.status_code in [400, 422]
```

#### 3. JWT 토큰 보안

```python
def test_jwt_expiration():
    """JWT 토큰 만료 테스트"""
    # 만료된 토큰 생성 (과거 시간)
    import jwt
    from datetime import datetime, timedelta

    expired_token = jwt.encode({
        "user_id": 123,
        "exp": datetime.utcnow() - timedelta(hours=1)
    }, "secret", algorithm="HS256")

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/credits/balance", headers=headers)

    assert response.status_code == 401
```

#### 4. Rate Limiting

```python
def test_rate_limiting():
    """Rate Limiting 테스트"""
    responses = []
    for _ in range(10):
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "wrong"
        })
        responses.append(response.status_code)

    # 429 (Too Many Requests) 응답 확인
    assert 429 in responses
```

### 보안 스캔 도구

```bash
# OWASP ZAP (자동 스캔)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8080

# Bandit (Python 코드 보안 취약점)
pip install bandit
bandit -r app/

# Safety (의존성 취약점 체크)
pip install safety
safety check
```

---

## 베타 테스트

### 베타 테스터 모집

#### 1. 베타 테스터 기준

- **목표 인원**: 10-20명
- **선정 기준**:
  - 영상 제작 경험자
  - IT 기술 이해도 높음
  - 피드백 제공 의향 있음

#### 2. 베타 테스트 설문지

**사전 설문**:
```
1. 영상 제작 경험이 있으신가요?
2. 어떤 용도로 영상을 제작하시나요?
3. 현재 사용 중인 영상 제작 도구는?
4. 기대하는 기능은 무엇인가요?
```

**사후 설문**:
```
1. 전반적인 사용 경험 (1-10점)
2. 가장 마음에 든 기능
3. 불편했던 점
4. 개선이 필요한 부분
5. 유료 전환 의향 (1-10점)
```

### 피드백 수집 채널

- **Google Forms**: 설문 조사
- **Slack/Discord**: 실시간 피드백
- **GitHub Issues**: 버그 리포트
- **Sentry**: 자동 에러 수집

---

## 테스트 자동화

### GitHub Actions 통합

**.github/workflows/tests.yml**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run E2E tests
        run: pytest tests/e2e/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 테스트 실행 스크립트

**scripts/run_tests.sh**:
```bash
#!/bin/bash

echo "🧪 Running all tests..."

# 단위 테스트
echo "📝 Unit tests..."
pytest tests/unit/ -v --cov=app --cov-report=xml

# 통합 테스트
echo "🔗 Integration tests..."
pytest tests/integration/ -v

# E2E 테스트
echo "🌐 E2E tests..."
pytest tests/e2e/ -v

# 보안 테스트
echo "🔒 Security tests..."
pytest -m security -v

# 커버리지 리포트
echo "📊 Coverage report..."
coverage html
echo "Open htmlcov/index.html to view coverage"

echo "✅ All tests completed!"
```

---

## 테스트 체크리스트

### 배포 전 필수 테스트

- [ ] 모든 단위 테스트 통과 (80% 커버리지)
- [ ] 통합 테스트 통과
- [ ] E2E 주요 시나리오 통과
- [ ] 보안 테스트 통과 (OWASP Top 10)
- [ ] 성능 테스트 통과 (100 동시 사용자)
- [ ] 부하 테스트 (P95 < 500ms)
- [ ] 헬스 체크 정상 작동
- [ ] 모니터링 메트릭 수집 확인
- [ ] 에러 추적 (Sentry) 작동 확인
- [ ] 데이터베이스 마이그레이션 테스트
- [ ] 백업/복구 테스트

### 베타 테스트 체크리스트

- [ ] 베타 테스터 10-20명 모집
- [ ] 사전 설문 완료
- [ ] 테스트 환경 제공
- [ ] 1-2주 테스트 기간
- [ ] 피드백 수집 (설문, 인터뷰)
- [ ] 버그 수정 및 개선
- [ ] 사후 설문 완료

---

## 📚 관련 문서

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 배포 가이드
- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - 모니터링
- [QUALITY_IMPROVEMENTS.md](./QUALITY_IMPROVEMENTS.md) - 품질 체크리스트

---

**문서 끝** 🦉
**다음 단계**: Week 6 Day 40-42 소프트 런칭
