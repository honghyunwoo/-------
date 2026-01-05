# 대본 템플릿 (45초 기준)

> **이 템플릿을 Claude Max / GPT Pro / Gemini Pro에 복사해서 대본을 생성하세요!**

---

## 프롬프트 (복사해서 사용)

```
스토아 철학 YouTube Shorts 대본을 작성해줘.

조건:
- 총 길이: 45초 이내 (약 200-250자)
- 구조: 훅(3초) → 명언(5초) → 해설(25초) → 적용(10초) → CTA(2초)
- 훅: 질문형 또는 충격형으로 시작
- 자막: 한 문장 15자 이내로 짧게
- 어조: 진지하지만 따뜻하게

명언: [여기에 명언 입력]
저자: [저자명]
출처: [출처]

JSON 형식으로 출력해줘:
{
  "hook": "훅 질문 (15자 이내)",
  "quote": "명언 원문",
  "author": "저자명",
  "explanation": "해설 (3-4문장, 각 15자 이내)",
  "application": "현대 적용 (2문장)",
  "cta": "마무리 (1문장)",
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "mood": "calm/dramatic/hopeful"
}
```

---

## 출력 예시 (이 형식으로 Claude에게 전달)

```json
{
  "hook": "왜 로마 황제는 매일 이 질문을 했을까?",
  "quote": "장애물이 곧 길이 된다.",
  "author": "마르쿠스 아우렐리우스",
  "explanation": "우리 앞의 장애물은 회피할 대상이 아닙니다. 그것을 통과하며 성장합니다. 역경이 최고의 스승입니다.",
  "application": "오늘 겪는 어려움을 기회로 바꿔보세요. 그 안에 답이 있습니다.",
  "cta": "더 많은 지혜를 원하신다면 구독해주세요.",
  "keywords": ["obstacle", "path", "stoic", "growth"],
  "mood": "dramatic"
}
```

---

## 길이 가이드

| 섹션 | 시간 | 글자 수 | 문장 수 |
|------|------|---------|---------|
| 훅 | 3초 | ~15자 | 1문장 |
| 명언 | 5초 | ~30자 | 1문장 |
| 해설 | 25초 | ~120자 | 3-4문장 |
| 적용 | 10초 | ~50자 | 2문장 |
| CTA | 2초 | ~15자 | 1문장 |
| **합계** | **45초** | **~230자** | **8-9문장** |

---

## 분위기(mood)별 키워드

| mood | 추천 B-roll |
|------|-------------|
| calm | meditation, ocean, sunset, nature |
| dramatic | storm, mountain, fire, thunder |
| hopeful | sunrise, growth, light, sky |
| reflective | water, fog, autumn, evening |

---

## 사용 방법

1. 위 프롬프트를 Claude Max/GPT/Gemini에 복사
2. 명언/저자/출처 부분만 변경
3. JSON 출력 받기
4. Claude Code에게 전달: "이 대본으로 영상 만들어줘"

**끝!**
