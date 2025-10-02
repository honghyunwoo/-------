# 🧹 기술 부채 정리 계획

**작업일**: 2025-10-03 (저녁)
**담당자**: Claude (수석 개발자)
**우선순위**: P1 (높음)

---

## 📋 현재 상황 분석

### 발견된 문제

#### 1. 중복 테스트 디렉토리
```
test/          - 12개 Python 파일
  ├── services/
  ├── integration/
  └── test_api.py

tests/         - 5개 Python 파일
  ├── e2e/
  └── test_api.py
```

**문제점**:
- 테스트가 두 곳에 분산
- test_api.py가 중복됨
- 혼란 야기

#### 2. 루트의 테스트 파일들
```
루트 디렉토리:
- test_auth.py
- test_full_video.py
- test_import.py
- test_phase1_quality.py
- test_server.py
- test_simple.py
- nul (쓸모없는 파일)
```

**문제점**:
- 테스트 파일이 루트에 산재
- 프로젝트 구조 오염

#### 3. 구버전 파일
```
- app/models/user_old.py (사용되지 않음)
```

#### 4. 파일명 표준 위반
```
- app/controllers/v1/1_Admin_Dashboard.py
  (숫자로 시작하는 파일명)
```

---

## 🎯 정리 계획

### Phase 1: 안전한 백업 (현재 커밋)
✅ 현재 상태를 Git으로 보존

### Phase 2: 구버전 파일 삭제
**작업**:
1. `app/models/user_old.py` 삭제
2. `nul` 파일 삭제

**검증**:
- import 참조 확인 완료 ✅ (참조 없음)

### Phase 3: 테스트 디렉토리 통합
**전략**: `test/` → `tests/` 통합

**작업 순서**:
1. `tests/` 디렉토리 구조 확인
2. `test/` 내용을 `tests/`로 이동
   - `test/services/` → `tests/unit/`
   - `test/integration/` → `tests/integration/`
   - `test/test_api.py` → 중복 확인 후 병합/삭제
3. import 경로 수정
4. 테스트 실행 검증

**최종 구조**:
```
tests/
├── __init__.py
├── unit/           # test/services/ 내용
├── integration/    # test/integration/ 내용
└── e2e/           # 기존 tests/e2e/ 유지
```

### Phase 4: 루트 테스트 파일 정리
**전략**: 유용한 것만 tests/로 이동, 나머지 삭제

**파일별 처리**:
1. `test_auth.py` → `tests/e2e/test_auth.py`
2. `test_server.py` → `tests/e2e/test_server.py`
3. `test_full_video.py` → `tests/e2e/test_full_video.py`
4. `test_phase1_quality.py` → 삭제 (일회성)
5. `test_import.py` → 삭제 (간단한 테스트)
6. `test_simple.py` → 삭제 (간단한 테스트)

### Phase 5: 파일명 표준화
**작업**:
```bash
mv app/controllers/v1/1_Admin_Dashboard.py \
   app/controllers/v1/admin_dashboard.py
```

**검증**:
- import 경로 수정
- 기능 테스트

---

## 🔍 상세 작업 단계

### Step 1: user_old.py 삭제 ✅

**검증 완료**:
```bash
$ grep -r "user_old" --include="*.py"
# 결과: 참조 없음 ✅
```

**작업**:
```bash
rm app/models/user_old.py
rm nul
```

### Step 2: 테스트 디렉토리 구조 파악

**test/ 내용**:
```
test/
├── __init__.py
├── services/
│   ├── test_hook_enhancer.py
│   ├── test_mrbeast_subtitle.py
│   ├── test_seo_optimizer.py
│   ├── test_task.py
│   ├── test_thumbnail_generator.py
│   ├── test_video.py
│   ├── test_voice.py
│   └── test_youtube_trend.py
├── integration/
│   └── test_viral_pipeline.py
└── test_api.py
```

**tests/ 내용**:
```
tests/
├── e2e/
│   ├── test_bitrate_fix.py
│   ├── test_full_pipeline.py
│   └── test_quality_verification.py
└── test_api.py (중복!)
```

### Step 3: 테스트 파일 중복 확인

**test/test_api.py vs tests/test_api.py**:
- 내용 비교 필요
- 더 완전한 버전 선택
- 나머지 삭제

### Step 4: Import 경로 영향 분석

**변경 전**:
```python
from test.services.test_task import ...
```

**변경 후**:
```python
from tests.unit.test_task import ...
```

**영향 받는 파일**:
- pytest 설정
- CI/CD 스크립트
- 문서

---

## ⚠️ 리스크 및 대응

### 리스크 1: 테스트 깨짐
**대응**: 각 단계마다 테스트 실행하여 검증

### 리스크 2: Import 오류
**대응**:
1. 전체 검색으로 import 찾기
2. 수정 후 검증
3. IDE에서 확인

### 리스크 3: CI/CD 영향
**대응**: pytest 명령어 확인 및 업데이트

---

## ✅ 검증 체크리스트

### 파일 삭제 후
- [ ] Git 상태 확인
- [ ] import 에러 없음
- [ ] 기능 테스트 통과

### 테스트 이동 후
- [ ] 모든 테스트 실행 성공
- [ ] import 경로 정상
- [ ] Coverage 유지

### 파일명 변경 후
- [ ] import 업데이트 완료
- [ ] 서버 정상 작동
- [ ] API 테스트 통과

---

## 📊 예상 결과

### 정리 전
```
루트: 7개 불필요 파일
test/: 12개 파일
tests/: 5개 파일
총: 24개 테스트 관련 파일 (분산됨)
```

### 정리 후
```
루트: 깔끔
tests/: 통합된 테스트 (체계적)
  ├── unit/ (8개)
  ├── integration/ (1개)
  └── e2e/ (6개)
총: 15개 파일 (통합됨, -9개)
```

---

## 🚀 실행 순서

1. ✅ 이 계획서 작성
2. ⏭️ user_old.py, nul 삭제
3. ⏭️ test_api.py 중복 확인
4. ⏭️ 테스트 디렉토리 통합
5. ⏭️ 루트 테스트 파일 정리
6. ⏭️ 파일명 표준화
7. ⏭️ import 경로 수정
8. ⏭️ 전체 테스트 실행
9. ⏭️ 커밋

**예상 소요 시간**: 2-3시간

---

**작성일**: 2025-10-03 19:30
**시작 예정**: 즉시
