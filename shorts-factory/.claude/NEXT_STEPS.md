# Shorts Factory - 다음 작업 방향

> **마지막 업데이트**: 2026-01-06
> **현재 버전**: 2.1.0
> **다음 목표**: 테스트 강화 + 콘텐츠 확장

---

## 우선순위별 작업 목록

### P1: 테스트 커버리지 확대 (25% → 80%)

**현황**: 3개 테스트 파일만 존재

| 모듈 | 테스트 파일 | 상태 |
|-----|------------|------|
| quote_loader | test_quote_loader.py | ✅ 완료 |
| broll_selector | test_broll_selector.py | ✅ 완료 |
| subtitle_generator | test_subtitle_generator.py | ✅ 완료 |
| tts_engine | - | ⏳ 필요 |
| ffmpeg_composer | - | ⏳ 필요 |
| video_composer | - | ⏳ 필요 |
| script_generator | - | ⏳ 필요 |
| script_validator | - | ⏳ 필요 |
| thumbnail_generator | - | ⏳ 필요 |
| upload_packager | - | ⏳ 필요 |

**작업 순서**:
1. `tests/test_tts_engine.py` - TTS 엔진 테스트
2. `tests/test_ffmpeg_composer.py` - 영상 합성 테스트
3. `tests/test_script_validator.py` - 스크립트 검증 테스트
4. `tests/test_thumbnail_generator.py` - 썸네일 테스트
5. `tests/test_upload_packager.py` - 패키징 테스트
6. `tests/test_pipeline_integration.py` - 통합 테스트

---

### P2: V3.0 스크립트 확장 (21초 → 45-55초)

**현황**: 각 문장 평균 12자, 총 21초

**목표**: 각 문장 40-70자, 총 45-55초

**확장 가이드**:

| 필드 | 현재 | 목표 | 확장 방법 |
|-----|------|------|----------|
| s1_hook | 12자 | 40-50자 | 질문 + 반전 암시 |
| s2_pain | 12자 | 50-60자 | 구체적 상황 + 감정 |
| s3_reframe | 12자 | 60-70자 | 인사이트 + 근거 |
| s4_insight | 12자 | 50-60자 | 단계별 행동 |
| s5_action | 12자 | 50-60자 | 전후 대비 |
| s6_loop_cta | 12자 | 30-40자 | 루프 + 기대감 |

**샘플 생성 후 A/B 테스트 필요**

---

### P3: 멀티플랫폼 배포

**지원 플랫폼**:
1. YouTube Shorts (현재)
2. TikTok
3. Instagram Reels

**필요 작업**:
- `upload_packager.py` 확장
- 플랫폼별 메타데이터 템플릿
- 해시태그 최적화
- 썸네일 비율 조정 (TikTok)

---

### P4: 코드 품질 개선

**1. 오류 처리 개선**
```python
# Before
except Exception as e:
    pass

# After
except FileNotFoundError:
    logger.error(f"파일 없음: {path}")
except json.JSONDecodeError:
    logger.error(f"JSON 파싱 실패: {path}")
```

**2. 로깅 표준화**
```python
# Before
print(f"[OK] TTS 생성 완료")

# After
logger.info("TTS 생성 완료")
```

**3. 설정 통합**
- `config/` 폴더 정리
- 중앙집중식 설정 로더 생성

---

## 빠른 시작 명령어

### 새 세션 시작 시

```bash
# 1. 프로젝트 폴더로 이동
cd C:\Users\hynoo\-------\shorts-factory

# 2. Git 상태 확인
git status

# 3. 테스트 실행
python -m pytest tests/ -v

# 4. 단일 영상 테스트
python scripts/batch_generate.py --id 1
```

### 배치 생성

```bash
# 순차 (안정)
python scripts/batch_generate.py --all

# 병렬 (빠름)
python scripts/batch_generate.py --all --parallel 4
```

---

## 참고 문서

| 문서 | 경로 | 내용 |
|-----|------|------|
| PRD | `docs/01_PRD.md` | 제품 요구사항 |
| 기술 설계 | `docs/04_TECHNICAL_DESIGN.md` | 아키텍처 |
| API 참조 | `docs/API_REFERENCE.md` | 모듈 API |
| 변경 이력 | `docs/CHANGELOG.md` | 버전 히스토리 |

---

## 의사결정 기록

| 날짜 | 주제 | 결정 | 이유 |
|-----|------|------|------|
| 2026-01-06 | 영상 합성 | FFmpeg + NVENC | 50x 성능 향상 |
| 2026-01-06 | TTS | Edge-TTS | 무료 + 고품질 |
| 2026-01-06 | 스크립트 | V2.1 (6문장) | 최적 흐름 |
| 2026-01-06 | 배치 처리 | ProcessPoolExecutor | 4x 속도 |
