# 🗄️ 올빼미 AI 영상 스튜디오 - 데이터베이스 마이그레이션 가이드

**작성자**: Claude (수석 개발자)
**작성일**: 2025-10-03
**목적**: Alembic 마이그레이션 시스템 사용 가이드

---

## 📚 목차
1. [마이그레이션 시스템 개요](#마이그레이션-시스템-개요)
2. [마이그레이션 명령어](#마이그레이션-명령어)
3. [마이그레이션 생성 가이드](#마이그레이션-생성-가이드)
4. [롤백 전략](#롤백-전략)
5. [베스트 프랙티스](#베스트-프랙티스)
6. [문제 해결](#문제-해결)

---

## 🎯 마이그레이션 시스템 개요

### 왜 Alembic인가?
- ✅ **스키마 버전 관리**: 데이터베이스 스키마 변경 이력 추적
- ✅ **안전한 배포**: 롤백 가능한 스키마 변경
- ✅ **팀 협업**: Git처럼 스키마 변경 공유
- ✅ **자동 생성**: SQLAlchemy 모델에서 자동으로 마이그레이션 생성

### 디렉토리 구조
```
MoneyPrinterTurbo/
├── alembic.ini                    # Alembic 설정 파일
├── migrations/                     # 마이그레이션 디렉토리
│   ├── env.py                     # 환경 설정 (DATABASE_URL 연동)
│   ├── script.py.mako             # 마이그레이션 템플릿
│   ├── README                     # Alembic 설명서
│   └── versions/                  # 마이그레이션 버전들
│       └── cc53309ef86d_initial_schema.py
├── app/
│   ├── database/
│   │   └── connection.py          # DATABASE_URL 정의
│   └── models/                    # SQLAlchemy 모델들
│       ├── __init__.py            # 모든 모델 import
│       ├── user.py
│       ├── subscription.py
│       ├── video_history.py
│       └── ...
```

### 설정 요약
- **DATABASE_URL**: `app/database/connection.py`에서 가져옴 (환경 변수)
- **target_metadata**: `Base.metadata` (모든 SQLAlchemy 모델 포함)
- **개발 환경**: SQLite (`owl_studio.db`)
- **프로덕션**: PostgreSQL (환경 변수로 설정)

---

## 🔧 마이그레이션 명령어

### 1. 현재 상태 확인
```bash
# 현재 적용된 마이그레이션 버전 확인
alembic current

# 출력 예시:
# cc53309ef86d (head)
```

### 2. 마이그레이션 히스토리 확인
```bash
# 모든 마이그레이션 히스토리 보기
alembic history

# 출력 예시:
# cc53309ef86d -> (head), initial schema
```

### 3. 최신 버전으로 업그레이드
```bash
# 최신 마이그레이션으로 업그레이드
alembic upgrade head

# 출력 예시:
# INFO  [alembic.runtime.migration] Running upgrade  -> cc53309ef86d, initial schema
```

### 4. 특정 버전으로 업그레이드
```bash
# 특정 리비전으로 업그레이드
alembic upgrade cc53309ef86d

# 또는 상대적 업그레이드 (+1 = 한 단계 위로)
alembic upgrade +1
```

### 5. 롤백 (다운그레이드)
```bash
# 한 단계 롤백
alembic downgrade -1

# 특정 버전으로 롤백
alembic downgrade cc53309ef86d

# 초기 상태로 완전 롤백
alembic downgrade base
```

### 6. SQL 미리보기 (DRY RUN)
```bash
# 실제 적용하지 않고 SQL만 출력
alembic upgrade head --sql

# 특정 범위의 SQL 출력
alembic upgrade base:head --sql > migration.sql
```

---

## 📝 마이그레이션 생성 가이드

### 자동 생성 (권장)
Alembic이 SQLAlchemy 모델 변경사항을 자동으로 감지하여 마이그레이션 생성

```bash
# 1. 모델 파일 수정 (예: app/models/user.py)
# 2. 마이그레이션 자동 생성
alembic revision --autogenerate -m "add email field to user"

# 3. 생성된 파일 검토
# migrations/versions/xxxxx_add_email_field_to_user.py
```

**주의사항**:
- 생성된 마이그레이션 파일을 **반드시 검토**하세요
- Alembic이 감지하지 못하는 변경사항도 있습니다
- 특히 컬럼 이름 변경, 데이터 타입 변경은 수동 확인 필요

### 수동 생성
복잡한 데이터 마이그레이션이나 Alembic이 감지하지 못하는 변경사항

```bash
# 빈 마이그레이션 파일 생성
alembic revision -m "custom data migration"

# 생성된 파일 수동 편집
# migrations/versions/xxxxx_custom_data_migration.py
```

**수동 마이그레이션 예시**:
```python
def upgrade():
    """Upgrade schema."""
    # 새 컬럼 추가
    op.add_column('users', sa.Column('full_name', sa.String(255)))

    # 기존 데이터 마이그레이션
    op.execute("""
        UPDATE users
        SET full_name = first_name || ' ' || last_name
        WHERE full_name IS NULL
    """)

    # NOT NULL 제약 조건 추가
    op.alter_column('users', 'full_name', nullable=False)

def downgrade():
    """Downgrade schema."""
    # 롤백: 컬럼 삭제
    op.drop_column('users', 'full_name')
```

---

## 🔄 롤백 전략

### 롤백 가능성 보장
모든 마이그레이션은 `upgrade()`와 `downgrade()` 함수를 모두 구현해야 합니다.

```python
def upgrade():
    """데이터베이스를 새 버전으로 업그레이드"""
    op.create_table('new_table', ...)

def downgrade():
    """이전 버전으로 롤백"""
    op.drop_table('new_table')
```

### 데이터 손실 주의
- **DROP TABLE**: 롤백 시 데이터 복구 불가능
- **DROP COLUMN**: 해당 컬럼 데이터 영구 손실
- **데이터 변환**: 원본 데이터 보존 전략 필요

### 안전한 롤백 전략
```python
def upgrade():
    """안전한 컬럼 추가"""
    # 1. 새 컬럼 추가 (NULL 허용)
    op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))

    # 2. 기존 데이터 마이그레이션
    op.execute("UPDATE users SET new_field = old_field WHERE new_field IS NULL")

    # 3. NOT NULL 제약 조건 추가
    op.alter_column('users', 'new_field', nullable=False)

def downgrade():
    """안전한 롤백"""
    # NOT NULL 제약 조건 제거 후 컬럼 삭제
    op.drop_column('users', 'new_field')
    # 주의: new_field 데이터는 영구 손실됨
```

### 프로덕션 롤백 체크리스트
- [ ] 백업 완료 확인
- [ ] downgrade() 함수 테스트 완료
- [ ] 데이터 손실 범위 파악
- [ ] 롤백 후 애플리케이션 호환성 확인
- [ ] 롤백 시간 추정 (대용량 테이블 주의)

---

## ✅ 베스트 프랙티스

### 1. 마이그레이션 이름 규칙
```bash
# 좋은 예시 (동사 + 대상)
alembic revision --autogenerate -m "add subscription plan to user"
alembic revision --autogenerate -m "rename video_path to video_url"
alembic revision --autogenerate -m "remove deprecated branding fields"

# 나쁜 예시
alembic revision -m "update"           # 너무 모호함
alembic revision -m "fix bug"          # 구체적이지 않음
```

### 2. 작은 단위로 자주 커밋
```bash
# ❌ 나쁜 예: 한 번에 많은 변경
# - 10개 테이블 수정
# - 수십 개 컬럼 추가/삭제
# → 롤백 시 모든 변경사항이 한 번에 되돌려짐

# ✅ 좋은 예: 작은 단위로 분리
# Migration 1: add email to user
# Migration 2: add subscription plan table
# Migration 3: add foreign key to user
# → 각 단계별로 롤백 가능
```

### 3. 프로덕션 배포 전 테스트
```bash
# 1. 개발 환경에서 테스트
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 2. 스테이징 환경에서 테스트
# - 프로덕션 데이터 복사본 사용
# - 실제 배포 시나리오 시뮬레이션

# 3. SQL 검토
alembic upgrade head --sql > review.sql
# review.sql 파일 검토 후 DBA 승인
```

### 4. 데이터 백업
```bash
# SQLite 백업
cp owl_studio.db owl_studio_backup_$(date +%Y%m%d).db

# PostgreSQL 백업
pg_dump owl_studio > backup_$(date +%Y%m%d).sql
```

### 5. 절대 수동으로 스키마 변경하지 않기
```sql
-- ❌ 절대 금지: 수동 SQL 실행
ALTER TABLE users ADD COLUMN new_field VARCHAR(100);

-- ✅ 올바른 방법: Alembic 마이그레이션 사용
-- alembic revision --autogenerate -m "add new_field to user"
```

### 6. Git과 함께 사용
```bash
# 마이그레이션 파일을 Git에 커밋
git add migrations/versions/xxxxx_add_email_to_user.py
git commit -m "feat: add email field to user model"

# 팀원들이 pull 후:
alembic upgrade head
```

---

## 🛠️ 문제 해결

### 문제 1: "Can't locate revision identified by 'xxxxx'"
**원인**: 로컬 데이터베이스가 Git의 최신 마이그레이션과 동기화되지 않음

**해결**:
```bash
# 1. 현재 상태 확인
alembic current

# 2. 모든 마이그레이션 히스토리 확인
alembic history

# 3. 강제로 특정 버전으로 설정 (주의!)
alembic stamp head  # 현재 DB를 최신 버전으로 간주

# 4. 또는 초기화 후 재적용
alembic downgrade base
alembic upgrade head
```

### 문제 2: "Target database is not up to date"
**원인**: 데이터베이스에 적용되지 않은 마이그레이션 존재

**해결**:
```bash
# 최신 버전으로 업그레이드
alembic upgrade head
```

### 문제 3: 마이그레이션 충돌 (Merge Heads)
**원인**: 여러 개발자가 동시에 마이그레이션 생성

**해결**:
```bash
# 1. 충돌 확인
alembic heads

# 2. 병합 마이그레이션 생성
alembic merge -m "merge heads" head1_id head2_id

# 3. 병합 마이그레이션 적용
alembic upgrade head
```

### 문제 4: "FAILED: Target database is not up to date"
**원인**: 환경 변수 설정 문제 또는 DATABASE_URL 불일치

**해결**:
```bash
# 1. .env 파일 확인
cat .env

# 2. DATABASE_URL이 올바른지 확인
echo $DATABASE_URL  # Linux/Mac
echo %DATABASE_URL%  # Windows

# 3. Python으로 직접 확인
python -c "from app.database.connection import DATABASE_URL; print(DATABASE_URL)"

# 4. 환경 변수 재설정
# .env 파일 수정 후 다시 시도
```

### 문제 5: autogenerate가 변경사항을 감지하지 못함
**원인**:
- 모델이 `Base`를 상속하지 않음
- `app/models/__init__.py`에 import되지 않음
- `migrations/env.py`의 target_metadata가 잘못 설정됨

**해결**:
```python
# 1. 모델이 Base를 상속하는지 확인
from app.database.connection import Base

class MyModel(Base):
    __tablename__ = 'my_table'
    # ...

# 2. app/models/__init__.py에 추가
from app.models.my_model import MyModel

__all__ = [
    'Base',
    'MyModel',
    # ...
]

# 3. migrations/env.py 확인
from app.models import *  # 모든 모델 import
target_metadata = Base.metadata  # 올바르게 설정되었는지 확인
```

---

## 📊 마이그레이션 히스토리

### 초기 마이그레이션 (cc53309ef86d)
**일자**: 2025-10-03
**제목**: "initial schema"

**변경사항**:
- ✅ `video_histories` 테이블 생성
- ✅ `video_generation_history` 테이블 제거 (구버전)
- ✅ `users` 테이블에 API 키 컬럼 추가:
  - `openai_api_key` (LargeBinary, 암호화됨)
  - `pexels_api_keys` (LargeBinary, 암호화됨)
  - `pixabay_api_keys` (LargeBinary, 암호화됨)

**롤백 가능**: ✅ Yes
**데이터 손실 위험**: ⚠️ `video_generation_history` 테이블의 기존 데이터는 롤백 시 복구 불가

---

## 🔗 관련 문서
- [PROJECT_MASTER_PLAN.md](./PROJECT_MASTER_PLAN.md) - Week 1 Task 5: 데이터베이스 마이그레이션
- [ERROR_TRACKING.md](./ERROR_TRACKING.md) - ERR-004: 데이터베이스 마이그레이션 부재
- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)

---

**마지막 업데이트**: 2025-10-03
**다음 리뷰**: 2025-10-10 (Week 2)

🦉 **올빼미 AI 영상 스튜디오** - 체계적인 데이터베이스 관리로 안정적인 서비스를!
