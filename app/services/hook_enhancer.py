#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
후킹 강화 알고리즘 모듈

이 모듈은 영상의 첫 3-8초를 최적화하여 시청자를 사로잡습니다:
1. 강력한 오프닝 문구 생성 (호기심 유발, 질문형, 충격)
2. 패턴 인터럽트 (예상 깨기, 반전)
3. 즉각적 가치 제시 (무엇을 얻을지 명확히)
4. 감정 자극 (공감, 두려움, 흥분)
5. 스토리 텔링 시작 (미완성 루프)
"""

import re
from typing import Dict, List, Optional, Tuple
from loguru import logger


class HookEnhancer:
    """후킹 강화 알고리즘"""

    def __init__(self):
        """초기화"""
        self.hook_patterns = {
            "curiosity": [
                "이것을 알게 되면 {topic}에 대한 생각이 완전히 바뀔 거예요",
                "{topic}에 대해 아무도 말하지 않는 진실",
                "대부분의 사람들이 {topic}에 대해 완전히 잘못 알고 있습니다",
                "{number}일 동안 {topic}을 시도한 결과, 충격적인 발견을 했습니다",
                "{topic}의 숨겨진 비밀이 드디어 밝혀졌습니다"
            ],
            "question": [
                "{topic}이 정말로 가능할까요?",
                "왜 아무도 {topic}에 대해 이렇게 말하지 않을까요?",
                "{topic}을 시도하기 전에 꼭 알아야 할 것은?",
                "{topic}으로 {benefit}을 얻을 수 있다면?",
                "만약 {topic}이 {opposite}라면 어떻게 될까요?"
            ],
            "shock": [
                "{topic}의 충격적인 진실을 발견했습니다",
                "이것은 {topic}에 대한 모든 것을 바꿔놓을 겁니다",
                "{topic}이 당신이 생각하는 것과 정반대일 수 있습니다",
                "{number}명 중 {number}명이 {topic}에 대해 모르는 사실",
                "{topic}에서 절대로 해서는 안 되는 {number}가지"
            ],
            "value": [
                "이 영상을 끝까지 보면 {benefit}을 얻게 됩니다",
                "{topic}으로 {benefit}하는 정확한 방법을 보여드립니다",
                "{time} 안에 {benefit}하는 법을 알려드릴게요",
                "{topic}의 가장 중요한 {number}가지를 공개합니다",
                "지금부터 {benefit}을 위한 단계별 가이드를 시작합니다"
            ],
            "emotion": [
                "제가 {topic}을 처음 시도했을 때, 믿을 수 없었습니다",
                "이것은 제 {life_aspect}을 완전히 바꿔놓았습니다",
                "당신도 {topic}에 대해 똑같은 실수를 하고 있나요?",
                "{topic}을 모르면 {negative_outcome}할 수 있습니다",
                "당신이 {topic}에서 성공하지 못한 진짜 이유"
            ],
            "story": [
                "{number}년 전, 저는 {topic}에 대해 아무것도 몰랐습니다",
                "이것은 {topic}에 대한 제 여정이 시작된 순간입니다",
                "오늘 제가 {topic}에서 발견한 것을 보여드리겠습니다",
                "{topic}을 {time} 동안 시도한 뒤, 모든 것이 바뀌었습니다",
                "이 영상은 {topic}에 대한 가장 솔직한 이야기입니다"
            ],
            "urgency": [
                "{topic}에 대해 지금 당장 알아야 하는 이유",
                "이것을 모르면 {topic}에서 뒤처질 수 있습니다",
                "{topic}이 {time} 안에 {change}할 예정입니다",
                "지금이 {topic}을 시작하기에 완벽한 시점입니다",
                "{topic}에서 앞서가기 위한 마지막 기회일 수 있습니다"
            ],
            "contrast": [
                "{topic}: 전문가들이 말하는 것 vs 실제 현실",
                "{topic}에 대한 가장 큰 오해와 진실",
                "{old_way} 대신 {new_way}를 해야 하는 이유",
                "대부분의 사람들은 {topic}을 이렇게 하지만, 틀렸습니다",
                "{topic}의 좋은 면과 나쁜 면을 모두 보여드립니다"
            ]
        }

        # MrBeast 스타일 패턴
        self.mrbeast_patterns = [
            "I spent {number} hours doing {topic} and this is what happened",
            "I gave away {number} {items} and you won't believe the results",
            "Last person to {action} wins {prize}",
            "I survived {number} days {challenge} and here's what I learned",
            "I tested {topic} for {time} straight and the results were shocking"
        ]

    def analyze_hook_strength(self, text: str) -> Dict[str, any]:
        """
        후킹 문구의 강도 분석

        Args:
            text: 분석할 텍스트

        Returns:
            분석 결과 딕셔너리
        """
        analysis = {
            "text": text,
            "length": len(text),
            "word_count": len(text.split()),
            "has_question": "?" in text,
            "has_numbers": bool(re.search(r'\d+', text)),
            "has_urgency": any(word in text.lower() for word in [
                "지금", "당장", "즉시", "바로", "오늘", "now", "today", "immediately"
            ]),
            "has_benefit": any(word in text.lower() for word in [
                "방법", "비법", "가이드", "단계", "팁", "비밀", "how to", "guide", "secret"
            ]),
            "has_emotion": any(word in text.lower() for word in [
                "충격", "놀라운", "믿을 수 없는", "완전히", "절대", "shocking", "amazing", "incredible"
            ]),
            "strength_score": 0.0
        }

        # 강도 점수 계산 (0-100)
        score = 0

        # 길이 점수 (50-100자가 이상적)
        if 30 <= analysis["length"] <= 120:
            score += 20
        elif 20 <= analysis["length"] <= 150:
            score += 10

        # 단어 수 점수 (7-15 단어가 이상적)
        if 5 <= analysis["word_count"] <= 20:
            score += 15

        # 질문 형식
        if analysis["has_question"]:
            score += 15

        # 숫자 포함 (구체성)
        if analysis["has_numbers"]:
            score += 15

        # 긴급성
        if analysis["has_urgency"]:
            score += 10

        # 혜택 제시
        if analysis["has_benefit"]:
            score += 15

        # 감정 자극
        if analysis["has_emotion"]:
            score += 10

        analysis["strength_score"] = min(score, 100)
        analysis["strength_level"] = self._get_strength_level(score)

        return analysis

    def _get_strength_level(self, score: float) -> str:
        """강도 레벨 반환"""
        if score >= 80:
            return "매우 강함"
        elif score >= 60:
            return "강함"
        elif score >= 40:
            return "보통"
        elif score >= 20:
            return "약함"
        else:
            return "매우 약함"

    def generate_hooks(
        self,
        topic: str,
        style: str = "curiosity",
        count: int = 5,
        language: str = "ko"
    ) -> List[Dict[str, any]]:
        """
        후킹 문구 생성

        Args:
            topic: 주제
            style: 스타일 (curiosity, question, shock, value, emotion, story, urgency, contrast)
            count: 생성할 개수
            language: 언어 (ko, en)

        Returns:
            후킹 문구 리스트
        """
        if style not in self.hook_patterns and style != "mrbeast":
            logger.warning(f"Unknown style: {style}, using 'curiosity'")
            style = "curiosity"

        hooks = []

        if style == "mrbeast":
            patterns = self.mrbeast_patterns
        else:
            patterns = self.hook_patterns.get(style, self.hook_patterns["curiosity"])

        # 패턴에서 랜덤하게 선택하거나 순환
        for i in range(min(count, len(patterns))):
            pattern = patterns[i % len(patterns)]

            # 패턴에 값 채우기
            hook_text = self._fill_pattern(pattern, topic, language)

            # 강도 분석
            analysis = self.analyze_hook_strength(hook_text)

            hooks.append({
                "text": hook_text,
                "style": style,
                "strength_score": analysis["strength_score"],
                "strength_level": analysis["strength_level"],
                "metadata": {
                    "has_question": analysis["has_question"],
                    "has_numbers": analysis["has_numbers"],
                    "has_urgency": analysis["has_urgency"],
                    "word_count": analysis["word_count"]
                }
            })

        # 강도 점수 기준 정렬 (높은 순)
        hooks.sort(key=lambda x: x["strength_score"], reverse=True)

        logger.info(f"Generated {len(hooks)} hooks for topic: {topic}")
        return hooks

    def _fill_pattern(self, pattern: str, topic: str, language: str) -> str:
        """패턴에 값 채우기"""
        replacements = {
            "{topic}": topic,
            "{number}": "3" if language == "ko" else "3",
            "{benefit}": "성공" if language == "ko" else "success",
            "{opposite}": "거짓" if language == "ko" else "false",
            "{time}": "10분" if language == "ko" else "10 minutes",
            "{life_aspect}": "삶" if language == "ko" else "life",
            "{negative_outcome}": "실패" if language == "ko" else "fail",
            "{change}": "변화" if language == "ko" else "change",
            "{old_way}": "기존 방식" if language == "ko" else "old way",
            "{new_way}": "새로운 방식" if language == "ko" else "new way",
            "{items}": "아이템" if language == "ko" else "items",
            "{action}": "액션" if language == "ko" else "action",
            "{prize}": "상금" if language == "ko" else "prize",
            "{challenge}": "도전" if language == "ko" else "challenge"
        }

        result = pattern
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result

    def optimize_opening(
        self,
        script: str,
        target_duration: float = 5.0,
        style: str = "curiosity"
    ) -> Dict[str, any]:
        """
        스크립트의 오프닝 최적화

        Args:
            script: 원본 스크립트
            target_duration: 목표 시간 (초)
            style: 후킹 스타일

        Returns:
            최적화된 오프닝 정보
        """
        # 스크립트를 문장으로 분리
        sentences = re.split(r'[.!?]\s+', script)
        first_sentence = sentences[0] if sentences else script[:100]

        # 주제 추출 (첫 문장에서)
        topic = self._extract_topic(first_sentence)

        # 강력한 후킹 생성
        hooks = self.generate_hooks(topic, style=style, count=3)

        # 최적화된 오프닝 구성
        best_hook = hooks[0] if hooks else {"text": first_sentence, "strength_score": 0}

        # 예상 말하기 시간 계산 (한국어: 분당 200-250자, 영어: 분당 150-160단어)
        chars_per_second = 4  # 한국어 기준
        estimated_duration = len(best_hook["text"]) / chars_per_second

        result = {
            "original_opening": first_sentence,
            "optimized_hook": best_hook["text"],
            "hook_style": style,
            "strength_score": best_hook["strength_score"],
            "estimated_duration": round(estimated_duration, 1),
            "target_duration": target_duration,
            "meets_target": estimated_duration <= target_duration,
            "alternative_hooks": [h["text"] for h in hooks[1:3]]
        }

        logger.info(f"Optimized opening: {result['strength_score']} strength score")
        return result

    def _extract_topic(self, text: str) -> str:
        """텍스트에서 주제 추출"""
        # 간단한 주제 추출 (첫 10단어 또는 50자)
        words = text.split()
        if len(words) > 10:
            return " ".join(words[:10])
        return text[:50] if len(text) > 50 else text

    def create_pattern_interrupt(
        self,
        topic: str,
        expectation: str = "일반적인 생각",
        reality: str = "실제 현실"
    ) -> Dict[str, str]:
        """
        패턴 인터럽트 생성 (예상 깨기)

        Args:
            topic: 주제
            expectation: 예상되는 것
            reality: 실제 현실

        Returns:
            패턴 인터럽트 문구
        """
        patterns = [
            f"대부분의 사람들은 {topic}에 대해 {expectation}이라고 생각합니다. 하지만 {reality}입니다.",
            f"{topic}에 대한 가장 큰 오해는 {expectation}입니다. 진실은 {reality}입니다.",
            f"만약 제가 {topic}이 {expectation}이 아니라 {reality}라고 말한다면?",
            f"{topic}: {expectation}이 아니라 {reality}인 이유",
            f"당신이 {topic}에 대해 알고 있는 것은 틀렸을 수 있습니다. {expectation}이 아니라 {reality}이기 때문입니다."
        ]

        return {
            "pattern_interrupt": patterns[0],
            "alternatives": patterns[1:],
            "structure": "expectation_vs_reality",
            "effectiveness": "high"
        }

    def generate_value_promise(
        self,
        topic: str,
        benefit: str,
        time_commitment: str = "5분"
    ) -> Dict[str, str]:
        """
        가치 약속 생성

        Args:
            topic: 주제
            benefit: 혜택
            time_commitment: 시간 투자

        Returns:
            가치 약속 문구
        """
        promises = [
            f"이 영상 {time_commitment}만 투자하면 {topic}으로 {benefit}하는 방법을 알게 됩니다.",
            f"{time_commitment} 뒤, 당신은 {topic}의 전문가가 될 겁니다. {benefit}을 보장합니다.",
            f"지금부터 {time_commitment} 동안 {topic}으로 {benefit}하는 정확한 단계를 보여드립니다.",
            f"{time_commitment}이면 충분합니다. {topic}으로 {benefit}하는 모든 것을 알려드립니다.",
            f"끝까지 보면 {topic}에서 {benefit}을 얻는 비법을 얻게 됩니다. {time_commitment}의 가치가 있습니다."
        ]

        return {
            "value_promise": promises[0],
            "alternatives": promises[1:],
            "structure": "time_benefit_specific",
            "cta_strength": "strong"
        }


def enhance_hook(
    script: str,
    style: str = "curiosity",
    target_duration: float = 5.0
) -> Dict[str, any]:
    """
    편의 함수: 스크립트의 후킹 강화

    Args:
        script: 원본 스크립트
        style: 후킹 스타일
        target_duration: 목표 시간 (초)

    Returns:
        강화된 후킹 정보
    """
    enhancer = HookEnhancer()
    return enhancer.optimize_opening(script, target_duration=target_duration, style=style)
