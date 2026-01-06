# Script V2 Guide - 대본 작성 가이드라인

> **버전**: 2.0
> **최종 수정**: 2026-01-06
> **목표**: 30-40초 영상, 공감과 행동 유도

---

## 1. 핵심 스펙

| 항목 | 기준 |
|------|------|
| 총 길이 | 30-40초 (225-285자) |
| 문장 수 | 6문장 (s1~s6) |
| 문장당 길이 | 30-55자 |
| 톤 | 반말, 단문, 구어체 |
| 화자 포지션 | "먼저 넘어진 동료" |

---

## 2. 6문장 구조

| 슬롯 | 역할 | 심리 원리 | 예시 |
|------|------|----------|------|
| **s1_hook** | 인지부조화 유발 | 예상 깨기 | "미루는 게 나쁜 게 아니야." |
| **s2_pain** | 고통 인정 | 공감 | "나도 그랬거든. 할 일 보기만 해도 숨 막혔어." |
| **s3_reframe** | 관점 전환 | 비난→이해 | "근데 그게 의지 문제가 아니더라고." |
| **s4_insight** | 핵심 통찰 | 손실회피 | "뇌가 '시작의 고통'을 피하려는 거래." |
| **s5_action** | 행동 제안 | 자기결정성 | "2분만 해보자. 진짜 2분." |
| **s6_loop_cta** | 루프 유도 | 정체성 강화 | CTA 3종 템플릿 사용 |

---

## 3. 운영 규칙 (4가지)

### 규칙 1: 문장당 1 아이디어
- 한 문장에 한 가지 메시지만
- 복문/중문 금지
- Bad: "미루는 건 의지 문제가 아니라 뇌가 고통을 회피하려는 거야."
- Good: "미루는 건 의지 문제가 아니야." + "뇌가 고통을 피하려는 거래."

### 규칙 2: 자막 밀도 상한
- 1문장 = 최대 2줄
- 55자 초과 시 분리 필수
- 영상 가독성 확보

### 규칙 3: S5 Action은 제안형
- "~해라" (X) 명령형 금지
- "~해보자" (O) 제안형 사용
- 자기결정성 보장

### 규칙 4: Loop CTA 3종 템플릿
```
인정형: "여기까지 본 너, 이미 달라지고 있어."
축하형: "오늘 이 영상 본 거, 그게 첫 걸음이야."
연결형: "같은 고민 가진 사람, 생각보다 많아. 우리 같이 가자."
```
- cta_type: "acknowledge" | "celebrate" | "connect"
- 3개 순환 사용

---

## 4. 금지 표현 목록

### 장면/화면 지칭 금지
- "이 영상", "지금 보고 있는", "화면에 보이는"
- 영상은 독립적으로 존재해야 함

### 의료/재정 표현 금지
- "치료", "약", "의사", "병원"
- "투자", "수익", "돈 벌기", "부자"

### 과장 표현 금지
- "인생이 바뀐다", "100% 효과"
- "놀라운", "충격적인", "믿을 수 없는"

### 클리셰 금지
- "성공의 비밀", "그들만의 방법"
- "단 하나의", "최고의"

### 명령형 금지 (S5)
- "~해라", "~하세요", "~해야 해"
- 대신: "~해보자", "~해볼까"

---

## 5. JSON 스키마 (V2)

```json
{
  "version": "v2",
  "id": 1,
  "category": "집중",
  "topic": "미루기 극복",
  "mood": "empathetic",
  "cta_type": "acknowledge",
  "s1_hook": "미루는 게 나쁜 게 아니야.",
  "s2_pain": "나도 그랬거든. 할 일 보기만 해도 숨 막혔어.",
  "s3_reframe": "근데 그게 의지 문제가 아니더라고.",
  "s4_insight": "뇌가 '시작의 고통'을 피하려는 거래.",
  "s5_action": "2분만 해보자. 진짜 2분.",
  "s6_loop_cta": "여기까지 본 너, 이미 달라지고 있어.",
  "broll_keywords": ["focus", "meditation", "sunrise"]
}
```

### 필드 규칙
| 필드 | 규칙 |
|------|------|
| version | "v2" 고정 |
| cta_type | "acknowledge" \| "celebrate" \| "connect" |
| mood | "empathetic" (기본) |
| broll_keywords | 영어 3개 정확히 |
| s1~s6 | 각 30-55자 |

---

## 6. 검증기 (Python)

```python
def validate_script_v2(script: dict) -> tuple[bool, list[str]]:
    """V2 스크립트 검증"""
    errors = []

    # 1. 버전 체크
    if script.get("version") != "v2":
        errors.append("version must be 'v2'")

    # 2. CTA 타입 체크
    valid_cta = ["acknowledge", "celebrate", "connect"]
    if script.get("cta_type") not in valid_cta:
        errors.append(f"cta_type must be one of {valid_cta}")

    # 3. broll_keywords 체크
    keywords = script.get("broll_keywords", [])
    if len(keywords) != 3:
        errors.append("broll_keywords must have exactly 3 items")
    if not all(kw.isascii() for kw in keywords):
        errors.append("broll_keywords must be English only")

    # 4. 문장 길이 체크
    sentences = ["s1_hook", "s2_pain", "s3_reframe",
                 "s4_insight", "s5_action", "s6_loop_cta"]
    for s in sentences:
        text = script.get(s, "")
        if not (30 <= len(text) <= 55):
            errors.append(f"{s}: {len(text)}자 (30-55자 필요)")

    # 5. 총 길이 체크
    total = sum(len(script.get(s, "")) for s in sentences)
    if not (225 <= total <= 285):
        errors.append(f"총 길이: {total}자 (225-285자 필요)")

    # 6. 금지 표현 체크
    forbidden = ["이 영상", "화면", "치료", "투자", "인생이 바뀐다",
                 "100%", "놀라운", "충격적인", "성공의 비밀"]
    full_text = " ".join(script.get(s, "") for s in sentences)
    for word in forbidden:
        if word in full_text:
            errors.append(f"금지 표현 포함: '{word}'")

    # 7. S5 제안형 체크
    s5 = script.get("s5_action", "")
    if any(x in s5 for x in ["해라", "하세요", "해야 해"]):
        errors.append("s5_action: 명령형 금지, 제안형 사용")

    return len(errors) == 0, errors
```

---

## 7. 예시 대본 (카테고리별)

### 집중 (Focus)
```json
{
  "version": "v2",
  "id": 1,
  "category": "집중",
  "topic": "미루기 극복",
  "mood": "empathetic",
  "cta_type": "acknowledge",
  "s1_hook": "미루는 게 나쁜 게 아니야.",
  "s2_pain": "나도 그랬거든. 할 일 보기만 해도 숨 막혔어.",
  "s3_reframe": "근데 그게 의지 문제가 아니더라고.",
  "s4_insight": "뇌가 '시작의 고통'을 피하려는 거래.",
  "s5_action": "2분만 해보자. 진짜 2분만.",
  "s6_loop_cta": "여기까지 본 너, 이미 달라지고 있어.",
  "broll_keywords": ["focus", "meditation", "sunrise"]
}
```

### 관계 (Relationship)
```json
{
  "version": "v2",
  "id": 2,
  "category": "관계",
  "topic": "거절의 기술",
  "mood": "empathetic",
  "cta_type": "celebrate",
  "s1_hook": "거절 못 하는 게 착한 게 아니야.",
  "s2_pain": "나도 그랬어. 싫은데 웃으면서 오케이 했지.",
  "s3_reframe": "근데 그게 상대 배려가 아니더라고.",
  "s4_insight": "진짜 배려는 솔직하게 말하는 거래.",
  "s5_action": "오늘 하나만 솔직하게 말해보자.",
  "s6_loop_cta": "오늘 이 영상 본 거, 그게 첫 걸음이야.",
  "broll_keywords": ["conversation", "hands", "coffee"]
}
```

---

## 8. 체크리스트

스크립트 작성 후 확인:

- [ ] 버전이 "v2"인가?
- [ ] 6문장 모두 30-55자인가?
- [ ] 총 길이 225-285자인가?
- [ ] cta_type이 3종 중 하나인가?
- [ ] broll_keywords가 영어 3개인가?
- [ ] 금지 표현이 없는가?
- [ ] S5가 제안형인가?
- [ ] 문장당 1 아이디어인가?

---

## 9. V1 → V2 마이그레이션

### 변경사항
| V1 | V2 |
|----|----|
| 21초, 120자 | 30-40초, 225-285자 |
| s3_insight | s3_reframe (관점전환) |
| s4_action | s4_insight (통찰) |
| s5_result | s5_action (행동제안) |
| 자유 CTA | 3종 템플릿 CTA |
| broll_keywords 자유 | 영어 3개 고정 |

### 기존 스크립트 변환
1. 문장 확장 (12자 → 40자 평균)
2. 구조 재배열 (reframe 추가)
3. CTA 템플릿 적용
4. 검증기 통과 확인
