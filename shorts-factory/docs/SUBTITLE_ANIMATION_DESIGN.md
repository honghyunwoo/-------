# 자막 애니메이션 설계 문서

> **Shorts Factory 자막 시스템 디자인 명세**

---

## 1. 현재 상태

### 기존 자막 시스템
- 정적 텍스트 오버레이
- 고정 위치 (하단 1600px)
- 단색 텍스트 + 테두리

### 개선 목표
- 단어별 하이라이트 (Word-by-word highlight)
- 부드러운 페이드 인/아웃
- 동적 위치 조정
- 핵심 단어 강조 효과

---

## 2. 애니메이션 유형

### Type A: 페이드 인/아웃 (기본)

```
시간: 0.0s ──────────────────────── 3.0s
투명도: 0% ─┐                    ┌─ 0%
           │    100% ─────────  │
           └─ 페이드 인 (0.2s)   └─ 페이드 아웃 (0.2s)
```

**구현:**
```python
txt_clip = txt_clip.with_effects([
    FadeIn(0.2),
    FadeOut(0.2)
])
```

### Type B: 슬라이드 인 (하단에서 위로)

```
위치:     화면 밖 → 목표 위치 → 화면 밖
시간:     0.0s      0.2s       2.8s     3.0s
```

**구현:**
```python
def slide_in(t):
    if t < 0.2:
        return ('center', 1920 - (1920 - target_y) * (t / 0.2))
    return ('center', target_y)

txt_clip = txt_clip.with_position(slide_in)
```

### Type C: 단어별 하이라이트 (핵심 기능)

```
"장애물이 곧 길이 된다"

시간 0.0s: [장애물이] 곧 길이 된다     ← 현재 단어 노란색
시간 0.5s: 장애물이 [곧] 길이 된다
시간 0.8s: 장애물이 곧 [길이] 된다
시간 1.2s: 장애물이 곧 길이 [된다]
```

**구현 전략:**
1. TTS 음성에서 단어별 타이밍 추출
2. 각 단어별로 별도 TextClip 생성
3. 현재 발화 중인 단어만 하이라이트 색상

---

## 3. 색상 팔레트

### 기본 스타일
```yaml
text_color: "#FFFFFF"           # 순백 (기본 텍스트)
highlight_color: "#D4AF37"      # 금색 (명언 강조)
stroke_color: "#000000"         # 검정 (테두리)
shadow_color: "rgba(0,0,0,0.5)" # 반투명 그림자
```

### 감정별 스타일
| 감정 | 텍스트 색상 | 강조 색상 |
|------|-------------|-----------|
| 중립 | 흰색 (#FFF) | 금색 (#D4AF37) |
| 역경 | 흰색 | 붉은 금색 (#CD853F) |
| 평화 | 흰색 | 청금색 (#4A90D9) |
| 희망 | 흰색 | 밝은 금색 (#FFD700) |

---

## 4. 위치 및 레이아웃

### 자막 영역

```
┌─────────────────────────────────────┐ 0px
│                                     │
│                                     │
│         (영상 콘텐츠 영역)           │
│                                     │
│                                     │
├─────────────────────────────────────┤ 1200px (안전 영역 시작)
│                                     │
│    ┌───────────────────────────┐    │
│    │                           │    │
│    │     "자막 텍스트"          │    │ 1400-1600px (자막 영역)
│    │                           │    │
│    └───────────────────────────┘    │
│                                     │
├─────────────────────────────────────┤ 1700px (안전 영역 끝)
│     [YouTube UI 영역 - 피해야 함]    │
└─────────────────────────────────────┘ 1920px
```

### 설정값
```python
SUBTITLE_SAFE_TOP = 1200      # 자막 최상단 한계
SUBTITLE_SAFE_BOTTOM = 1700   # 자막 최하단 한계
SUBTITLE_DEFAULT_Y = 1600     # 기본 Y 위치
SUBTITLE_MARGIN = 320         # 하단 여백 (1920 - 1600)
```

---

## 5. 타이포그래피

### 폰트 선택
| 용도 | 폰트 | 크기 | 굵기 |
|------|------|------|------|
| 기본 자막 | Malgun Gothic | 48px | Regular |
| 명언 강조 | Noto Serif KR | 52px | Bold |
| 숫자/영어 | Roboto | 48px | Medium |

### 줄바꿈 규칙
```python
MAX_CHARS_PER_LINE = 15     # 한 줄 최대 글자 수
MAX_LINES = 3               # 최대 줄 수
WRAP_WIDTH = 22             # textwrap 너비
```

---

## 6. 구현 계획

### Phase 1: 기본 애니메이션 (1-2주)
- [x] 페이드 인/아웃 효과
- [ ] 부드러운 등장/퇴장
- [ ] 그림자 효과 추가

### Phase 2: 단어별 하이라이트 (2-3주)
- [ ] TTS 타이밍 데이터 파싱
- [ ] 단어별 TextClip 분리
- [ ] 하이라이트 색상 전환
- [ ] 성능 최적화 (다수 클립 합성)

### Phase 3: 고급 효과 (3-4주)
- [ ] Ken Burns 효과 연동
- [ ] 감정별 색상 자동 적용
- [ ] 화면 전환 효과

---

## 7. 코드 구조

### 새 모듈 구조
```
core/
├── subtitle_generator.py     # 기존: SRT 생성
├── subtitle_animator.py      # 신규: 애니메이션 효과
└── subtitle_styles.py        # 신규: 스타일 정의
```

### SubtitleAnimator 클래스

```python
class SubtitleAnimator:
    """자막 애니메이션 처리기"""

    def __init__(self, style: SubtitleStyle = None):
        self.style = style or SubtitleStyle()

    def create_animated_clip(
        self,
        text: str,
        start: float,
        duration: float,
        animation: str = "fade"  # fade, slide, highlight
    ) -> VideoClip:
        """애니메이션이 적용된 자막 클립 생성"""
        pass

    def create_word_highlight_clips(
        self,
        text: str,
        word_timings: List[Tuple[str, float, float]],
        start: float
    ) -> List[VideoClip]:
        """단어별 하이라이트 클립 생성"""
        pass
```

---

## 8. 참고 자료

### 성공 사례 분석
- **Stoic Bond**: 금색 강조, 미니멀 디자인
- **Daily Stoic**: 세리프 폰트, 중앙 정렬
- **Einzelgänger**: 영화 자막 스타일, 하단 고정

### 기술 문서
- MoviePy 2.x TextClip: https://zulko.github.io/moviepy/
- Edge TTS 타이밍: https://github.com/rany2/edge-tts
