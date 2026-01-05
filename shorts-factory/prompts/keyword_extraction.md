# 키워드 추출 프롬프트

## 목적
스크립트의 각 문장에서 Pexels B-roll 검색에 적합한 영어 키워드를 추출합니다.

---

## 프롬프트

```
당신은 YouTube Shorts B-roll 매칭 전문가입니다.

아래 스크립트의 각 문장에 대해 Pexels 영상 검색에 적합한 영어 키워드를 추출해주세요.

### 규칙:
1. 각 문장당 2-3개의 키워드
2. 영어로 출력 (Pexels 검색용)
3. 추상적이고 시각적인 단어 선호
4. Stoic/철학 테마에 어울리는 키워드
5. 이미 사용한 키워드는 피하기 (아래 목록 참고)

### 좋은 키워드 예시:
- 자연: storm, ocean, mountain, sunrise, sunset, forest, rain
- 조각상: statue, sculpture, marble, greek, roman
- 감정: calm, peace, strength, power, resilience
- 시간: time, clock, hourglass, seasons
- 우주: universe, stars, galaxy, cosmos
- 불/빛: fire, flame, candle, light, shadow

### 피해야 할 키워드:
- 너무 구체적인 것 (예: "marcus aurelius face")
- 저작권 우려 (예: 브랜드명, 영화 제목)
- 검색 결과가 적은 것

### 이미 사용한 키워드:
{used_keywords_list}

### 스크립트:
{script_text}

### 출력 형식 (JSON):
[
  {
    "sentence": "문장 텍스트",
    "start_time": "0:00",
    "end_time": "0:05",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "mood": "calm/intense/inspiring/dark"
  },
  ...
]
```

---

## 사용 방법

1. `history/used_keywords.json`에서 이미 사용한 키워드 목록 가져오기
2. 위 프롬프트의 `{used_keywords_list}`와 `{script_text}` 치환
3. Claude에게 요청
4. 결과를 `workflow/current_project.json`의 `keywords` 필드에 저장

---

## 예시

### 입력 스크립트:
```
지금 겪고 있는 그 최악의 상황, 사실 당신이 직접 주문한 메뉴라면 어떨까요?
"운명이 가져다주는 것을 마치 자신이 선택한 것처럼 사랑하라." - 마르쿠스 아우렐리우스
```

### 출력:
```json
[
  {
    "sentence": "지금 겪고 있는 그 최악의 상황...",
    "start_time": "0:00",
    "end_time": "0:07",
    "keywords": ["storm", "challenge", "crossroads"],
    "mood": "intense"
  },
  {
    "sentence": "운명이 가져다주는 것을...",
    "start_time": "0:07",
    "end_time": "0:20",
    "keywords": ["fate", "embrace", "roman statue"],
    "mood": "inspiring"
  }
]
```

---

## 키워드 카테고리 가이드

| 스크립트 주제 | 추천 키워드 |
|--------------|-------------|
| 역경/시련 | storm, thunder, rain, waves, climb |
| 평화/명상 | calm, meditation, zen, peaceful, still water |
| 힘/강인함 | strength, power, lion, mountain, rock |
| 시간/인내 | time, hourglass, seasons, patience, growth |
| 지혜/철학 | books, library, statue, ancient, wisdom |
| 자연 순환 | sunrise, sunset, seasons, ocean, forest |
| 불/열정 | fire, flame, candle, spark, burning |
| 우주/광대함 | universe, stars, cosmos, galaxy, space |
