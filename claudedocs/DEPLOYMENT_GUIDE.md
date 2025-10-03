# 🚀 올빼미 AI 영상 스튜디오 - 배포 가이드

**작성일**: 2025-10-03
**버전**: 1.0
**대상**: Week 5 Day 29-35

---

## 📋 목차

1. [배포 아키텍처](#배포-아키텍처)
2. [사전 준비](#사전-준비)
3. [Docker 배포](#docker-배포)
4. [AWS 배포 (Terraform)](#aws-배포-terraform)
5. [CI/CD 파이프라인](#cicd-파이프라인)
6. [환경 변수 설정](#환경-변수-설정)
7. [모니터링 설정](#모니터링-설정)
8. [백업 및 복구](#백업-및-복구)
9. [트러블슈팅](#트러블슈팅)

---

## 배포 아키텍처

### 🏗️ 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                    CloudFront CDN                       │
│              (Static Assets & Videos)                   │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                   EC2 Instance                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Containers                               │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │ FastAPI API  │  │ Streamlit UI │             │  │
│  │  │  (Port 8080) │  │  (Port 8501) │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────┬──────────────────┘
                   │                  │
    ┌──────────────┴──────┐   ┌──────▼──────────┐
    │  RDS PostgreSQL     │   │ ElastiCache     │
    │   (Database)        │   │  (Redis Cache)  │
    └─────────────────────┘   └─────────────────┘
                   │
           ┌───────▼────────┐
           │   S3 Bucket    │
           │ (Video Files)  │
           └────────────────┘
```

### 📊 인프라 스펙

| 컴포넌트 | 스펙 | 비고 |
|----------|------|------|
| **EC2** | t3.medium (2 vCPU, 4GB RAM) | 개발용, 프로덕션은 t3.large 권장 |
| **RDS** | db.t3.micro (PostgreSQL 15) | 개발용, 프로덕션은 db.t3.small 이상 |
| **ElastiCache** | cache.t3.micro (Redis 7) | 개발용, 프로덕션은 cache.t3.small 권장 |
| **S3** | Standard Storage | 영상 파일 저장 |
| **CloudFront** | Global CDN | 영상 배포 가속화 |

---

## 사전 준비

### 1. AWS 계정 생성 및 설정

```bash
# AWS CLI 설치 (Windows)
winget install Amazon.AWSCLI

# AWS 자격 증명 설정
aws configure
# AWS Access Key ID: [입력]
# AWS Secret Access Key: [입력]
# Default region: ap-northeast-2
# Default output format: json
```

### 2. 필요한 도구 설치

```bash
# Docker Desktop (Windows)
winget install Docker.DockerDesktop

# Terraform
winget install Hashicorp.Terraform

# Git
winget install Git.Git
```

### 3. SSH 키 페어 생성

```bash
# AWS EC2 키 페어 생성
aws ec2 create-key-pair \
  --key-name owl-studio-key \
  --query 'KeyMaterial' \
  --output text > owl-studio-key.pem

# 권한 설정 (Linux/Mac)
chmod 400 owl-studio-key.pem
```

### 4. 도메인 구매 (선택)

- Route 53에서 도메인 구매: `owl-studio.kr`
- 또는 기존 도메인 사용

---

## Docker 배포

### 로컬 개발 환경

#### 1. .env 파일 생성

```bash
cp .env.example .env
# .env 파일 편집하여 실제 값 입력
```

#### 2. Docker Compose로 실행

```bash
# 빌드 및 시작
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps

# 종료
docker-compose down
```

#### 3. 서비스 접속

- **FastAPI**: http://localhost:8080
- **Streamlit**: http://localhost:8501
- **API 문서**: http://localhost:8080/api/docs
- **Health Check**: http://localhost:8080/health
- **Prometheus**: http://localhost:8080/metrics

### 프로덕션 배포 (단일 서버)

```bash
# 프로덕션용 .env 파일 생성
cat > .env << EOF
APP_ENV=production
USE_SQLITE=false
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_HOST=redis
SENTRY_DSN=your-sentry-dsn
# ... 기타 환경 변수
EOF

# 프로덕션 모드로 실행
docker-compose -f docker-compose.yml up -d
```

---

## AWS 배포 (Terraform)

### 1. Terraform 초기화

```bash
cd terraform

# Terraform 초기화
terraform init

# 실행 계획 확인
terraform plan
```

### 2. 변수 파일 생성

```bash
# terraform.tfvars 파일 생성
cat > terraform.tfvars << EOF
aws_region         = "ap-northeast-2"
environment        = "production"
project_name       = "owl-studio"
ec2_instance_type  = "t3.medium"
ec2_key_name       = "owl-studio-key"
rds_instance_class = "db.t3.small"
db_username        = "owl_user"
db_password        = "your-secure-password"
redis_node_type    = "cache.t3.small"
ssh_allowed_ips    = ["your-ip/32"]
EOF
```

### 3. 인프라 배포

```bash
# 인프라 생성
terraform apply

# 출력 확인
terraform output

# 주요 출력 값:
# - ec2_public_ip: EC2 서버 IP
# - rds_endpoint: PostgreSQL 엔드포인트
# - redis_endpoint: Redis 엔드포인트
# - cloudfront_url: CDN URL
```

### 4. EC2 서버 접속 및 애플리케이션 배포

```bash
# EC2 접속
ssh -i owl-studio-key.pem ubuntu@<ec2_public_ip>

# 애플리케이션 저장소 클론
git clone https://github.com/your-org/owl-studio.git /opt/owl-studio
cd /opt/owl-studio

# .env 파일 생성 (Terraform outputs 참조)
cat > .env << EOF
APP_ENV=production
USE_SQLITE=false
DATABASE_URL=<terraform output rds_endpoint>
REDIS_HOST=<terraform output redis_endpoint>
# ... 기타 환경 변수
EOF

# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 5. 데이터베이스 마이그레이션

```bash
# 컨테이너 내부 접속
docker exec -it owl-studio-api bash

# Alembic 마이그레이션 실행
alembic upgrade head

# 확인
alembic current
```

---

## CI/CD 파이프라인

### GitHub Actions 설정

#### 1. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions

필요한 Secrets:
```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-token
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
SLACK_WEBHOOK=your-slack-webhook-url
```

#### 2. 워크플로우 파일

이미 생성된 `.github/workflows/ci-cd.yml` 사용

#### 3. 배포 프로세스

```
코드 Push → GitHub
    ↓
Lint & Test (자동)
    ↓
Docker Build (자동)
    ↓
Push to Docker Hub (자동)
    ↓
Deploy to Staging (develop 브랜치)
    or
Deploy to Production (main 브랜치)
    ↓
Smoke Tests (자동)
    ↓
Slack Notification
```

### 수동 배포

```bash
# Staging 배포
git checkout develop
git pull origin develop
# GitHub Actions가 자동으로 배포

# Production 배포
git checkout main
git merge develop
git push origin main
# GitHub Actions가 자동으로 배포
```

---

## 환경 변수 설정

### 필수 환경 변수

```bash
# 애플리케이션 설정
APP_ENV=production
USE_SQLITE=false
DEBUG=false
LOG_LEVEL=INFO

# 데이터베이스
DATABASE_URL=postgresql://user:pass@host:5432/owl_studio

# Redis
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_PASSWORD=redis-password

# JWT 인증
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API 키
OPENAI_API_KEY=sk-...
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=koreacentral

# 결제
TOSS_PAYMENTS_SECRET_KEY=test_sk_...
TOSS_PAYMENTS_CLIENT_KEY=test_ck_...

# 모니터링
SENTRY_DSN=https://...@sentry.io/...

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=owl-studio-videos-production
AWS_REGION=ap-northeast-2
```

### 환경별 설정

**개발 환경** (`.env.development`):
```bash
APP_ENV=development
USE_SQLITE=true
DEBUG=true
LOG_LEVEL=DEBUG
```

**스테이징 환경** (`.env.staging`):
```bash
APP_ENV=staging
USE_SQLITE=false
DEBUG=true
LOG_LEVEL=INFO
```

**프로덕션 환경** (`.env.production`):
```bash
APP_ENV=production
USE_SQLITE=false
DEBUG=false
LOG_LEVEL=WARNING
```

---

## 모니터링 설정

### 1. Sentry 설정

```bash
# Sentry 프로젝트 생성
# https://sentry.io/

# DSN 발급 후 .env에 추가
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# 앱 시작 시 자동으로 Sentry 초기화됨
```

### 2. Prometheus + Grafana (선택)

```bash
# docker-compose에 모니터링 프로파일 추가하여 실행
docker-compose --profile with-monitoring up -d

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

### 3. CloudWatch 로그 (AWS)

```bash
# CloudWatch Logs 에이전트 설치
sudo apt-get install amazon-cloudwatch-agent

# 로그 그룹 생성
aws logs create-log-group --log-group-name /owl-studio/api

# 로그 스트림 생성
aws logs create-log-stream \
  --log-group-name /owl-studio/api \
  --log-stream-name production
```

---

## 백업 및 복구

### 데이터베이스 백업

#### 자동 백업 (RDS)

```bash
# RDS 자동 백업은 Terraform에서 설정됨
# backup_retention_period = 7 (7일간 보관)
```

#### 수동 백업

```bash
# PostgreSQL 덤프
docker exec owl-studio-db pg_dump \
  -U owl_user \
  -d owl_studio \
  > backup_$(date +%Y%m%d).sql

# S3에 업로드
aws s3 cp backup_$(date +%Y%m%d).sql \
  s3://owl-studio-backups/database/
```

### 데이터베이스 복구

```bash
# SQL 파일에서 복구
docker exec -i owl-studio-db psql \
  -U owl_user \
  -d owl_studio \
  < backup_20251003.sql
```

### 영상 파일 백업

```bash
# S3 버킷 간 동기화
aws s3 sync \
  s3://owl-studio-videos-production \
  s3://owl-studio-videos-backup \
  --storage-class GLACIER
```

---

## 트러블슈팅

### 일반적인 문제

#### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs api

# 일반적인 원인:
# - .env 파일 누락
# - 포트 충돌
# - 의존성 컨테이너 미실행
```

#### 2. 데이터베이스 연결 실패

```bash
# RDS 보안 그룹 확인
# EC2 → RDS 5432 포트 인바운드 허용 확인

# 연결 테스트
docker exec owl-studio-api python -c "
from app.database.db import get_db
db = next(get_db())
print('DB Connected!')
"
```

#### 3. Redis 연결 실패

```bash
# Redis 상태 확인
docker exec owl-studio-redis redis-cli ping
# 응답: PONG

# ElastiCache 보안 그룹 확인
# EC2 → ElastiCache 6379 포트 인바운드 허용 확인
```

#### 4. 메모리 부족

```bash
# Docker 메모리 제한 늘리기
# docker-compose.yml에 추가:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 5. 디스크 공간 부족

```bash
# Docker 정리
docker system prune -a --volumes

# 로그 파일 정리
find logs/ -name "*.log" -mtime +7 -delete
```

### 성능 문제

#### 1. API 응답 느림

```bash
# Prometheus 메트릭 확인
curl http://localhost:8080/metrics | grep http_request_duration

# 느린 요청 로그 확인
grep "Slow request" logs/app_$(date +%Y-%m-%d).log
```

#### 2. 데이터베이스 쿼리 느림

```bash
# PostgreSQL 슬로우 쿼리 로그 활성화
docker exec owl-studio-db psql -U owl_user -c \
  "ALTER SYSTEM SET log_min_duration_statement = 1000;"

# 재시작
docker restart owl-studio-db
```

---

## 보안 체크리스트

### 배포 전 필수 확인

- [ ] 모든 시크릿이 환경 변수로 분리됨
- [ ] .env 파일이 .gitignore에 포함됨
- [ ] JWT_SECRET_KEY 재생성 (강력한 무작위 값)
- [ ] DB 비밀번호 강력하게 설정 (20자 이상)
- [ ] SSH 키 페어 안전하게 보관
- [ ] RDS 퍼블릭 액세스 비활성화
- [ ] ElastiCache VPC 내부에서만 접근
- [ ] S3 버킷 퍼블릭 액세스 최소화
- [ ] CloudFront HTTPS only 설정
- [ ] Security Group 최소 권한 원칙

### 런칭 후 확인

- [ ] Sentry 에러 추적 작동 확인
- [ ] Prometheus 메트릭 수집 확인
- [ ] 백업 스크립트 정상 작동 확인
- [ ] SSL/TLS 인증서 설정 확인
- [ ] CORS 설정 확인
- [ ] Rate Limiting 작동 확인

---

## 📚 관련 문서

- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - 모니터링 설정
- [DATABASE_MIGRATION_GUIDE.md](./DATABASE_MIGRATION_GUIDE.md) - DB 마이그레이션
- [QUALITY_IMPROVEMENTS.md](./QUALITY_IMPROVEMENTS.md) - 품질 체크리스트
- [SYSTEM_AUDIT_REPORT.md](./SYSTEM_AUDIT_REPORT.md) - 전체 시스템 점검

---

**문서 끝** 🦉
**다음 단계**: Week 6 테스트 및 런칭
