# 프로젝트 현재 상태

> 마지막 업데이트: 2026-01-04

## 완료된 작업

### 2026-01-04 정리 작업
1. **올빼미 SaaS 코드 제거** (commit: 54ec6e5)
   - 164개 파일, 28,176줄 삭제
   - app/, webui/, migrations/, terraform/, tests/ 삭제
   - 올빼미 관련 설정 파일 삭제

2. **requirements.txt 정리** (commit: bc91c3e)
   - 패키지명 오류 수정 (google.generativeai → google-generativeai)
   - 중복 제거, 미사용 패키지 제거

3. **문서 정리** (commit: ae5ad90)
   - claudedocs/ 폴더 삭제 (21개 파일)
   - 빈 플레이스홀더 문서 삭제

4. **브랜치 정리**
   - fix-cli-bugs 머지 및 삭제
   - plan-repo-restructure 삭제

---

## 현재 프로젝트 구조

```
-------/
├── .claude/
│   ├── state.json          # 프로젝트 상태
│   └── CURRENT_STATUS.md   # 이 문서
├── .gitignore
├── LICENSE
├── README.md
├── docs/
│   ├── STOICFLOW_ARCHITECTURE_2026.md
│   ├── YOUTUBE_API_설정_가이드.md
│   └── voice-list.txt
├── resource/               # 공용 에셋
│   ├── fonts/ (142MB)
│   └── songs/ (56MB)
├── shorts-factory/         # ✅ 즉시 사용 가능
│   ├── main.py            # CLI 진입점
│   ├── pipeline.py        # 파이프라인 오케스트레이터
│   ├── gui_app.py         # GUI 앱
│   ├── core/              # 핵심 모듈
│   │   ├── quote_loader.py
│   │   ├── script_generator.py
│   │   ├── tts_engine.py
│   │   ├── subtitle_generator.py
│   │   ├── broll_selector.py
│   │   ├── video_composer.py
│   │   ├── metadata_generator.py
│   │   └── review_loop.py
│   ├── templates/
│   ├── assets/
│   ├── config/
│   └── output/
└── stoicflow/              # 🔨 미래 확장 베이스
    ├── pyproject.toml
    └── src/stoicflow/
        ├── domain/         # 엔티티, 값 객체
        ├── application/    # Use Cases, 인터페이스
        ├── infrastructure/ # 외부 연동 (LLM, TTS, YouTube)
        └── presentation/   # CLI, GUI, API
```

---

## 모듈별 상태

### shorts-factory (즉시 사용)
| 파일 | 줄 수 | 상태 |
|------|-------|------|
| main.py | 577 | ✅ 완료 |
| pipeline.py | 438 | ✅ 완료 |
| core/* | ~2,500 | ✅ 완료 |

**사용법:**
```bash
cd shorts-factory
python main.py setup
python main.py run 1
```

### stoicflow (미래 확장)
| 레이어 | 구현 상태 |
|--------|----------|
| domain | ✅ 엔티티 정의됨 |
| application | ⚠️ 인터페이스만 |
| infrastructure | ⚠️ 일부 어댑터 |
| presentation | ⚠️ CLI 스켈레톤 |

**예정 기능:**
- YouTube 자동 업로드
- 스케줄링 시스템
- 성과 분석

---

## 다음 작업 (우선순위)

### 🔴 즉시 (P0)
1. shorts-factory로 첫 쇼츠 5개 제작
2. YouTube 채널 생성 및 업로드

### 🟡 곧 (P1)
3. 성과 데이터 분석 (조회수, 시청 지속 시간)
4. 파이프라인 튜닝 (효과적인 훅/CTA 발견)

### 🟢 나중에 (P2)
5. StoicFlow에 YouTube 자동 업로드 추가
6. 스케줄링 시스템 구현
7. Shorts Factory → StoicFlow 점진적 마이그레이션

---

## 주의사항

### 하지 말 것
- ❌ Shorts Factory 아키텍처 리팩터링 (동작하면 OK)
- ❌ 불필요한 추상화 추가
- ❌ StoicFlow 완성 전에 Shorts Factory 삭제

### 할 것
- ✅ 쇼츠 만들기에 집중
- ✅ 데이터 수집 후 자동화 개선
- ✅ 점진적 StoicFlow 개발
