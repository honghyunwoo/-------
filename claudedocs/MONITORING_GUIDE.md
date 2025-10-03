# 🔍 올빼미 AI 영상 스튜디오 - 모니터링 가이드

**작성일**: 2025-10-03
**버전**: 1.0
**담당**: Week 4 Day 22-23

## 📋 목차

1. [개요](#개요)
2. [Sentry 에러 추적](#sentry-에러-추적)
3. [Prometheus 성능 모니터링](#prometheus-성능-모니터링)
4. [로깅 시스템](#로깅-시스템)
5. [모니터링 대시보드](#모니터링-대시보드)
6. [알림 설정](#알림-설정)
7. [운영 가이드](#운영-가이드)

---

## 개요

### 🎯 모니터링 목표

- **실시간 에러 추적**: Sentry를 통한 즉각적인 에러 감지
- **성능 모니터링**: Prometheus 메트릭으로 병목 지점 파악
- **사용자 추적**: 사용자 활동 및 세션 모니터링
- **시스템 헬스 체크**: 서비스 상태 실시간 확인

### 🛠️ 모니터링 스택

| 도구 | 목적 | 위치 |
|------|------|------|
| **Sentry** | 에러 추적 및 성능 모니터링 | `app/monitoring/sentry_config.py` |
| **Prometheus** | 메트릭 수집 및 성능 측정 | `app/middleware/monitoring.py` |
| **Loguru** | 구조화된 로깅 | `app/config/logging.py` |
| **FastAPI Middleware** | 요청/응답 모니터링 | `app/middleware/monitoring.py` |

---

## Sentry 에러 추적

### 🔧 초기 설정

**1. Sentry 계정 생성**
```bash
# https://sentry.io/ 에서 계정 생성
# 프로젝트 생성 후 DSN 발급
```

**2. 환경 변수 설정**
```bash
# .env 파일에 추가
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
APP_ENV=production
```

**3. 자동 초기화**
앱 시작 시 자동으로 Sentry가 초기화됩니다:

```python
# app/asgi.py에서 자동 실행
@app.on_event("startup")
async def startup_event():
    init_sentry(
        environment=os.getenv("APP_ENV", "development"),
        traces_sample_rate=0.1,  # 10% 트랜잭션 샘플링
        profiles_sample_rate=0.1,  # 10% 프로파일 샘플링
    )
```

### 📊 Sentry 기능

#### 1. 자동 에러 캡처
모든 처리되지 않은 예외가 자동으로 Sentry로 전송됩니다.

#### 2. 성능 트랜잭션 추적
FastAPI 엔드포인트별 성능 자동 추적:
- 요청 처리 시간
- 데이터베이스 쿼리 시간
- Redis 작업 시간

#### 3. Breadcrumb 추적
요청 흐름 자동 기록:
```python
# 요청마다 자동 breadcrumb 추가
{
    "message": "POST /api/videos/generate",
    "category": "http",
    "level": "info",
    "data": {
        "url": "http://localhost:8080/api/videos/generate",
        "method": "POST",
        "client_host": "127.0.0.1"
    }
}
```

#### 4. 민감 정보 필터링
자동으로 민감 정보를 제거:
- `password`, `token`, `api_key`, `secret`
- `authorization`, `cookie`, `session`
- `credit_card`, `ssn`

**예시**:
```python
# 원본 헤더
{"Authorization": "Bearer abc123...", "X-API-Key": "secret"}

# Sentry로 전송되는 데이터
{"Authorization": "[REDACTED]", "X-API-Key": "[REDACTED]"}
```

### 🔨 수동 에러 캡처

**특정 에러 캡처**:
```python
from app.monitoring.sentry_config import capture_exception

try:
    risky_operation()
except Exception as e:
    capture_exception(
        e,
        context={
            "user_id": user.id,
            "operation": "video_generation",
            "credits_used": 10
        }
    )
    raise
```

**메시지 로그**:
```python
from app.monitoring.sentry_config import capture_message

capture_message(
    "Unusual user behavior detected",
    level="warning",
    extra={
        "user_id": user.id,
        "behavior": "rapid_api_calls"
    }
)
```

### 👤 사용자 컨텍스트

**사용자 정보 설정**:
```python
from app.monitoring.sentry_config import set_user

set_user(
    user_id=user.id,
    email=user.email,
    username=user.username
)
```

**태그 추가**:
```python
from app.monitoring.sentry_config import set_tag

set_tag("subscription_tier", user.subscription_tier)
set_tag("video_quality", "premium")
```

---

## Prometheus 성능 모니터링

### 📈 수집 메트릭

#### 1. HTTP 요청 메트릭

**총 요청 수** (`http_requests_total`):
```python
# 메트릭 구조
http_requests_total{method="POST", endpoint="/api/videos/generate", status_code="200"} 150
```

**요청 처리 시간** (`http_request_duration_seconds`):
```python
# Histogram 버킷
http_request_duration_seconds_bucket{method="POST", endpoint="/api/videos/generate", le="0.1"} 50
http_request_duration_seconds_bucket{method="POST", endpoint="/api/videos/generate", le="0.5"} 120
http_request_duration_seconds_bucket{method="POST", endpoint="/api/videos/generate", le="1.0"} 140
```

**진행 중인 요청** (`http_requests_in_progress`):
```python
# 현재 처리 중인 요청 수
http_requests_in_progress{method="POST", endpoint="/api/videos/generate"} 5
```

**느린 요청 수** (`http_slow_requests_total`):
```python
# 2초 이상 걸린 요청 수
http_slow_requests_total{method="POST", endpoint="/api/videos/generate"} 10
```

#### 2. 데이터베이스 메트릭

**쿼리 실행 시간** (`db_query_duration_seconds`):
```python
from app.middleware.monitoring import log_db_query

# 쿼리 시작 전
start_time = time.time()

# 쿼리 실행
result = db.query(Video).all()

# 쿼리 종료 후 로깅
duration = time.time() - start_time
log_db_query("SELECT", duration)
```

#### 3. 사용자 메트릭

**활성 사용자 수** (`active_users_total`):
```python
from app.middleware.monitoring import update_active_users

# 현재 활성 사용자 수 업데이트
active_count = db.query(User).filter(User.is_active == 1).count()
update_active_users(active_count)
```

### 🔍 메트릭 조회

**Prometheus 엔드포인트**:
```bash
GET http://localhost:8080/metrics
```

**응답 예시**:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/videos/generate",status_code="200"} 150.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="POST",endpoint="/api/videos/generate",le="0.01"} 10.0
http_request_duration_seconds_bucket{method="POST",endpoint="/api/videos/generate",le="0.05"} 50.0
http_request_duration_seconds_bucket{method="POST",endpoint="/api/videos/generate",le="0.1"} 100.0
```

### 📊 Grafana 대시보드 (선택)

**1. Prometheus 연동**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'owl-studio'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**2. Grafana 대시보드 import**:
- Dashboard ID: 추후 제공 예정
- 또는 수동으로 패널 구성

---

## 로깅 시스템

### 📝 로그 레벨

| 레벨 | 용도 | 예시 |
|------|------|------|
| **DEBUG** | 상세 디버깅 정보 | `logger.debug(f"User {user_id} requested video generation")` |
| **INFO** | 일반 정보 | `logger.info(f"Video generation completed: {video_id}")` |
| **WARNING** | 경고 (동작은 정상) | `logger.warning(f"Slow query detected: {duration}s")` |
| **ERROR** | 에러 (복구 가능) | `logger.error(f"API call failed: {error}")` |
| **CRITICAL** | 치명적 에러 | `logger.critical(f"Database connection lost")` |

### 📂 로그 파일 구조

```
logs/
├── app_2025-10-03.log              # 일반 로그 (모든 레벨)
├── errors.log                      # 에러 전용 로그
├── app_json_2025-10-03.log         # JSON 형식 (분석용)
├── app_2025-10-02.log.zip          # 압축된 과거 로그
└── app_2025-10-01.log.zip
```

### 🔄 로그 rotation 설정

**일반 로그**:
- **Rotation**: 매일 자정 (00:00)
- **Retention**: 30일
- **Compression**: ZIP

**에러 로그**:
- **Rotation**: 100MB 크기마다
- **Retention**: 최근 10개 파일
- **Compression**: ZIP

**JSON 로그**:
- **Rotation**: 매일 자정
- **Retention**: 7일
- **Compression**: ZIP
- **Format**: JSON 직렬화

### 📊 로그 조회

**일반 로그 조회**:
```bash
# 최근 100줄
tail -n 100 logs/app_2025-10-03.log

# 실시간 모니터링
tail -f logs/app_2025-10-03.log

# 에러만 필터링
grep ERROR logs/app_2025-10-03.log
```

**JSON 로그 분석**:
```bash
# jq로 파싱
cat logs/app_json_2025-10-03.log | jq '.[] | select(.level == "ERROR")'

# 특정 사용자 로그
cat logs/app_json_2025-10-03.log | jq '.[] | select(.extra.user_id == 123)'
```

---

## 모니터링 대시보드

### 🖥️ 헬스 체크 엔드포인트

**기본 헬스 체크**:
```bash
GET http://localhost:8080/health
```

**응답**:
```json
{
    "status": "ok"
}
```

**Prometheus 메트릭**:
```bash
GET http://localhost:8080/metrics
```

### 📈 주요 모니터링 지표

#### 1. 응답 시간 모니터링
```bash
# X-Process-Time 헤더 확인
curl -I http://localhost:8080/api/videos/generate
# X-Process-Time: 0.523
```

#### 2. 느린 요청 감지
로그에서 자동으로 경고:
```
[WARNING] Slow request detected: POST /api/videos/generate (2.34s) - Status: 200
```

#### 3. 에러율 추적
```bash
# Prometheus 쿼리
rate(http_requests_total{status_code=~"5.."}[5m])
```

---

## 알림 설정

### 🚨 Sentry 알림

**1. 이메일 알림 설정**:
- Sentry 대시보드 → Settings → Alerts
- 알림 규칙 생성:
  - 조건: Error 발생 시
  - 빈도: 즉시 (또는 5분마다 요약)

**2. Slack 통합**:
```bash
# Sentry → Settings → Integrations → Slack
# Webhook URL 설정 후 채널 선택
```

**3. 알림 예시**:
```
🚨 [Production] New Error in owl-studio
Error: VideoGenerationError
Message: Failed to generate video: API quota exceeded
User: user@example.com (ID: 123)
Endpoint: POST /api/videos/generate
First seen: 2025-10-03 14:30:00 KST
```

### 📊 Prometheus 알림

**Alertmanager 설정** (선택):
```yaml
# alertmanager.yml
route:
  receiver: 'slack'

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#owl-studio-alerts'
```

**알림 규칙**:
```yaml
# prometheus_rules.yml
groups:
  - name: owl_studio_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponses
        expr: rate(http_slow_requests_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Many slow requests detected"
```

---

## 운영 가이드

### 🔍 일일 모니터링 체크리스트

**매일 확인 사항**:
- [ ] Sentry 대시보드에서 새로운 에러 확인
- [ ] Prometheus 메트릭에서 느린 요청 확인
- [ ] 에러 로그(`errors.log`) 검토
- [ ] 디스크 사용량 확인 (로그 파일 크기)

### 🚨 긴급 대응 절차

**1. 에러 급증 시**:
```bash
# 1. 최근 에러 로그 확인
tail -n 200 logs/errors.log

# 2. Sentry 대시보드 확인
# https://sentry.io/organizations/your-org/issues/

# 3. 영향 범위 파악
grep "ERROR" logs/app_2025-10-03.log | wc -l

# 4. 원인 분석 및 조치
```

**2. 성능 저하 시**:
```bash
# 1. 느린 요청 확인
grep "Slow request" logs/app_2025-10-03.log

# 2. Prometheus 메트릭 확인
curl http://localhost:8080/metrics | grep http_request_duration

# 3. 데이터베이스 쿼리 확인
grep "Slow database query" logs/app_2025-10-03.log
```

### 📈 성능 최적화 팁

**1. 느린 엔드포인트 식별**:
```python
# Prometheus 쿼리
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)
```

**2. 데이터베이스 쿼리 최적화**:
```bash
# 느린 쿼리 로그 확인
grep "Slow database query" logs/app_2025-10-03.log

# 1초 이상 걸린 쿼리 찾기
grep "Slow database query" logs/app_2025-10-03.log | grep -oP '\(\d+\.\d+s\)' | sort -rn
```

**3. 캐싱 적용**:
- Redis 캐싱 (Week 4 Day 26-28)
- 응답 압축 활성화
- CDN 통합

### 🔒 보안 모니터링

**1. 비정상적인 활동 감지**:
```python
# 빈번한 실패 로그인 시도
grep "Login failed" logs/app_2025-10-03.log | wc -l

# 비정상적인 API 호출 패턴
grep "RateLimitError" logs/app_2025-10-03.log
```

**2. Sentry에서 확인**:
- 반복되는 에러 패턴
- 특정 IP에서의 집중 요청
- 비정상적인 사용자 행동

### 📊 주간/월간 리포트

**성능 리포트 생성**:
```bash
# 1. 에러율 계산
total_requests=$(grep "POST\|GET" logs/app_2025-10-*.log | wc -l)
error_requests=$(grep "ERROR" logs/app_2025-10-*.log | wc -l)
error_rate=$(echo "scale=4; $error_requests / $total_requests * 100" | bc)

echo "Error Rate: $error_rate%"

# 2. 평균 응답 시간 추출
grep "X-Process-Time" logs/app_2025-10-*.log | \
  awk '{sum+=$NF; count++} END {print "Avg Response Time:", sum/count, "s"}'
```

---

## 🎯 다음 단계 (Week 4 Day 24-28)

### Day 24-25: 성능 모니터링 고도화
- [ ] APM (Application Performance Monitoring) 통합
- [ ] 커스텀 성능 대시보드 구축
- [ ] 실시간 알림 시스템 구축

### Day 26-28: 성능 최적화
- [ ] 데이터베이스 쿼리 최적화
- [ ] Redis 캐싱 구현
- [ ] CDN 통합
- [ ] 응답 압축 활성화

---

## 📚 참고 자료

### 공식 문서
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Loguru Documentation](https://loguru.readthedocs.io/)

### 추가 학습
- [Prometheus 쿼리 언어 (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana 대시보드 구성](https://grafana.com/docs/grafana/latest/dashboards/)
- [FastAPI 모니터링 Best Practices](https://fastapi.tiangolo.com/advanced/monitoring/)

---

## ✅ 체크리스트

### 설정 완료 확인
- [ ] `.env`에 `SENTRY_DSN` 설정
- [ ] `.env`에 `APP_ENV` 설정 (development/production)
- [ ] Sentry 프로젝트 생성 및 DSN 발급
- [ ] `/health` 엔드포인트 정상 작동 확인
- [ ] `/metrics` 엔드포인트 정상 작동 확인
- [ ] 로그 파일 rotation 확인

### 테스트 확인
- [ ] 에러 발생 시 Sentry로 자동 전송 확인
- [ ] Prometheus 메트릭 수집 확인
- [ ] 느린 요청 감지 및 로깅 확인
- [ ] 민감 정보 필터링 동작 확인

---

**문서 끝** 🦉
