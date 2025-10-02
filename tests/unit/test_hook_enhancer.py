#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
후킹 강화 알고리즘 모듈 테스트
"""
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.hook_enhancer import HookEnhancer, enhance_hook


class TestHookEnhancer(unittest.TestCase):
    """후킹 강화 알고리즘 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.enhancer = HookEnhancer()
        self.test_topic = "AI 영상 제작"

    def test_initialization(self):
        """초기화 테스트"""
        enhancer = HookEnhancer()
        self.assertIsNotNone(enhancer)
        self.assertIn("curiosity", enhancer.hook_patterns)
        self.assertIn("question", enhancer.hook_patterns)
        self.assertTrue(len(enhancer.mrbeast_patterns) > 0)

    def test_analyze_hook_strength_basic(self):
        """기본 후킹 강도 분석 테스트"""
        text = "이것을 알게 되면 AI에 대한 생각이 완전히 바뀔 거예요"
        analysis = self.enhancer.analyze_hook_strength(text)

        self.assertIsInstance(analysis, dict)
        self.assertIn("text", analysis)
        self.assertIn("strength_score", analysis)
        self.assertIn("strength_level", analysis)
        self.assertGreaterEqual(analysis["strength_score"], 0)
        self.assertLessEqual(analysis["strength_score"], 100)

    def test_analyze_hook_strength_with_question(self):
        """질문형 후킹 강도 분석 테스트"""
        text = "AI가 정말로 인간의 일자리를 대체할까요?"
        analysis = self.enhancer.analyze_hook_strength(text)

        self.assertTrue(analysis["has_question"])
        self.assertGreater(analysis["strength_score"], 30)

    def test_analyze_hook_strength_with_numbers(self):
        """숫자 포함 후킹 강도 분석 테스트"""
        text = "3일 만에 AI로 수익을 낸 방법"
        analysis = self.enhancer.analyze_hook_strength(text)

        self.assertTrue(analysis["has_numbers"])
        self.assertGreater(analysis["strength_score"], 20)

    def test_analyze_hook_strength_with_urgency(self):
        """긴급성 포함 후킹 강도 분석 테스트"""
        text = "지금 당장 알아야 하는 AI의 비밀"
        analysis = self.enhancer.analyze_hook_strength(text)

        self.assertTrue(analysis["has_urgency"])
        self.assertGreater(analysis["strength_score"], 30)

    def test_generate_hooks_curiosity(self):
        """호기심 스타일 후킹 생성 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="curiosity",
            count=5
        )

        self.assertIsInstance(hooks, list)
        self.assertEqual(len(hooks), 5)
        self.assertTrue(all(isinstance(h, dict) for h in hooks))
        self.assertTrue(all("text" in h for h in hooks))
        self.assertTrue(all("strength_score" in h for h in hooks))

    def test_generate_hooks_question(self):
        """질문 스타일 후킹 생성 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="question",
            count=3
        )

        self.assertIsInstance(hooks, list)
        self.assertEqual(len(hooks), 3)
        # 최소 하나는 물음표를 포함해야 함
        has_question = any("?" in h["text"] for h in hooks)
        self.assertTrue(has_question)

    def test_generate_hooks_shock(self):
        """충격 스타일 후킹 생성 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="shock",
            count=3
        )

        self.assertIsInstance(hooks, list)
        self.assertEqual(len(hooks), 3)
        self.assertTrue(all(h["style"] == "shock" for h in hooks))

    def test_generate_hooks_value(self):
        """가치 제시 스타일 후킹 생성 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="value",
            count=3
        )

        self.assertIsInstance(hooks, list)
        self.assertEqual(len(hooks), 3)
        self.assertTrue(all(h["style"] == "value" for h in hooks))

    def test_generate_hooks_sorted_by_strength(self):
        """후킹 강도 순 정렬 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="curiosity",
            count=5
        )

        # 강도 점수가 내림차순으로 정렬되어 있어야 함
        scores = [h["strength_score"] for h in hooks]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_generate_hooks_mrbeast_style(self):
        """MrBeast 스타일 후킹 생성 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic="challenge",
            style="mrbeast",
            count=3,
            language="en"
        )

        self.assertIsInstance(hooks, list)
        self.assertTrue(len(hooks) > 0)
        self.assertTrue(all(h["style"] == "mrbeast" for h in hooks))

    def test_optimize_opening_basic(self):
        """기본 오프닝 최적화 테스트"""
        script = "오늘은 AI로 영상을 만드는 방법에 대해 알아보겠습니다. 먼저 준비물이 필요합니다."
        result = self.enhancer.optimize_opening(script)

        self.assertIsInstance(result, dict)
        self.assertIn("original_opening", result)
        self.assertIn("optimized_hook", result)
        self.assertIn("strength_score", result)
        self.assertIn("estimated_duration", result)
        self.assertGreater(result["strength_score"], 0)

    def test_optimize_opening_with_style(self):
        """스타일 지정 오프닝 최적화 테스트"""
        script = "AI 영상 제작의 모든 것을 알려드립니다."
        result = self.enhancer.optimize_opening(
            script,
            target_duration=5.0,
            style="question"
        )

        self.assertEqual(result["hook_style"], "question")
        self.assertIsNotNone(result["optimized_hook"])

    def test_optimize_opening_duration_check(self):
        """오프닝 시간 체크 테스트"""
        script = "AI로 쉽게 영상 만들기"
        result = self.enhancer.optimize_opening(
            script,
            target_duration=10.0
        )

        self.assertIn("meets_target", result)
        self.assertIsInstance(result["meets_target"], bool)
        self.assertLessEqual(result["estimated_duration"], 20.0)

    def test_create_pattern_interrupt(self):
        """패턴 인터럽트 생성 테스트"""
        result = self.enhancer.create_pattern_interrupt(
            topic="AI 영상 제작",
            expectation="어렵다",
            reality="쉽다"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("pattern_interrupt", result)
        self.assertIn("alternatives", result)
        self.assertIn("structure", result)
        self.assertIn("어렵다", result["pattern_interrupt"])
        self.assertIn("쉽다", result["pattern_interrupt"])

    def test_generate_value_promise(self):
        """가치 약속 생성 테스트"""
        result = self.enhancer.generate_value_promise(
            topic="AI 영상 제작",
            benefit="전문가 수준의 영상을 만들",
            time_commitment="10분"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("value_promise", result)
        self.assertIn("alternatives", result)
        self.assertIn("10분", result["value_promise"])
        self.assertIn("AI 영상 제작", result["value_promise"])

    def test_strength_level_categorization(self):
        """강도 레벨 분류 테스트"""
        # 매우 강함
        level_high = self.enhancer._get_strength_level(85)
        self.assertEqual(level_high, "매우 강함")

        # 강함
        level_strong = self.enhancer._get_strength_level(65)
        self.assertEqual(level_strong, "강함")

        # 보통
        level_medium = self.enhancer._get_strength_level(45)
        self.assertEqual(level_medium, "보통")

        # 약함
        level_weak = self.enhancer._get_strength_level(25)
        self.assertEqual(level_weak, "약함")

        # 매우 약함
        level_very_weak = self.enhancer._get_strength_level(10)
        self.assertEqual(level_very_weak, "매우 약함")

    def test_extract_topic(self):
        """주제 추출 테스트"""
        text = "오늘은 AI 영상 제작에 대해 알아보는 시간을 가져보겠습니다"
        topic = self.enhancer._extract_topic(text)

        self.assertIsInstance(topic, str)
        self.assertTrue(len(topic) > 0)
        self.assertLessEqual(len(topic), 100)

    def test_hook_metadata(self):
        """후킹 메타데이터 테스트"""
        hooks = self.enhancer.generate_hooks(
            topic=self.test_topic,
            style="urgency",
            count=3
        )

        for hook in hooks:
            self.assertIn("metadata", hook)
            metadata = hook["metadata"]
            self.assertIn("has_question", metadata)
            self.assertIn("has_numbers", metadata)
            self.assertIn("has_urgency", metadata)
            self.assertIn("word_count", metadata)


class TestHookEnhancerIntegration(unittest.TestCase):
    """후킹 강화 통합 테스트"""

    def test_enhance_hook_convenience_function(self):
        """편의 함수 테스트"""
        script = "AI로 영상을 쉽게 만드는 방법을 알려드립니다."
        result = enhance_hook(script, style="curiosity", target_duration=5.0)

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_hook", result)
        self.assertIn("strength_score", result)

    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        enhancer = HookEnhancer()

        # 1. 여러 스타일의 후킹 생성
        curiosity_hooks = enhancer.generate_hooks("AI", style="curiosity", count=2)
        question_hooks = enhancer.generate_hooks("AI", style="question", count=2)
        shock_hooks = enhancer.generate_hooks("AI", style="shock", count=2)

        # 2. 스크립트 최적화
        script = "AI 영상 제작 가이드입니다."
        optimized = enhancer.optimize_opening(script, style="value")

        # 3. 패턴 인터럽트 생성
        pattern = enhancer.create_pattern_interrupt("AI", "복잡하다", "간단하다")

        # 4. 가치 약속 생성
        promise = enhancer.generate_value_promise("AI", "프로 수준", "5분")

        # 모든 결과가 유효한지 확인
        self.assertTrue(len(curiosity_hooks) == 2)
        self.assertTrue(len(question_hooks) == 2)
        self.assertTrue(len(shock_hooks) == 2)
        self.assertIsNotNone(optimized["optimized_hook"])
        self.assertIsNotNone(pattern["pattern_interrupt"])
        self.assertIsNotNone(promise["value_promise"])

    def test_multiple_styles_comparison(self):
        """여러 스타일 비교 테스트"""
        styles = ["curiosity", "question", "shock", "value", "emotion"]
        topic = "AI 영상 제작"

        results = {}
        for style in styles:
            hooks = HookEnhancer().generate_hooks(topic, style=style, count=1)
            if hooks:
                results[style] = hooks[0]["strength_score"]

        # 모든 스타일이 후킹을 생성했는지 확인
        self.assertEqual(len(results), len(styles))
        # 모든 점수가 0보다 큰지 확인
        self.assertTrue(all(score > 0 for score in results.values()))


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.services.test_hook_enhancer.TestHookEnhancer.test_generate_hooks_curiosity
    unittest.main()
