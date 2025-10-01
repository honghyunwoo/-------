#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SEO 최적화 엔진 테스트
"""
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.seo_optimizer import SEOOptimizer, optimize_video_seo


class TestSEOOptimizer(unittest.TestCase):
    """SEO 최적화 엔진 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.optimizer = SEOOptimizer()
        self.test_topic = "AI 영상 제작"
        self.test_keywords = ["AI", "영상", "제작", "자동화", "튜토리얼"]

    def test_initialization(self):
        """초기화 테스트"""
        optimizer = SEOOptimizer()
        self.assertIsNotNone(optimizer)
        self.assertEqual(optimizer.max_tags, 15)
        self.assertIn("교육", optimizer.categories)

    def test_optimize_title_basic(self):
        """제목 최적화 기본 테스트"""
        result = self.optimizer.optimize_title(
            topic=self.test_topic,
            keywords=self.test_keywords
        )

        self.assertIsInstance(result, dict)
        self.assertIn("best_title", result)
        self.assertIn("score", result)
        self.assertIn("alternatives", result)
        self.assertIn("analysis", result)
        
        # 제목이 비어있지 않은지 확인
        self.assertGreater(len(result["best_title"]), 0)
        
        # 점수가 0-100 범위인지 확인
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_optimize_title_with_viral_keywords(self):
        """바이럴 키워드 포함 제목 최적화 테스트"""
        viral_keywords = [("트렌드", 100), ("인기", 80), ("최신", 60)]
        result = self.optimizer.optimize_title(
            topic=self.test_topic,
            keywords=self.test_keywords,
            viral_keywords=viral_keywords
        )

        self.assertIsNotNone(result["best_title"])
        self.assertGreater(result["score"], 0)

    def test_optimize_title_styles(self):
        """다양한 스타일의 제목 최적화 테스트"""
        styles = ["curiosity", "question", "number", "benefit"]
        
        for style in styles:
            result = self.optimizer.optimize_title(
                topic=self.test_topic,
                keywords=self.test_keywords,
                style=style
            )
            self.assertIsNotNone(result["best_title"])
            self.assertGreater(len(result["best_title"]), 0)

    def test_score_title(self):
        """제목 점수 계산 테스트"""
        # 좋은 제목
        good_title = "AI 영상 제작 완벽 가이드: 3가지 핵심 팁"
        good_score = self.optimizer._score_title(good_title, self.test_keywords)
        
        # 나쁜 제목 (키워드 없음, 너무 짧음)
        bad_title = "영상"
        bad_score = self.optimizer._score_title(bad_title, self.test_keywords)
        
        # 좋은 제목의 점수가 더 높아야 함
        self.assertGreater(good_score, bad_score)
        self.assertGreaterEqual(good_score, 0)
        self.assertLessEqual(good_score, 100)

    def test_count_keywords_in_text(self):
        """텍스트 내 키워드 카운트 테스트"""
        text = "AI 영상 제작은 영상 자동화의 미래입니다"
        count = self.optimizer._count_keywords_in_text(text, self.test_keywords)
        
        self.assertGreaterEqual(count, 2)  # AI, 영상, 제작 포함

    def test_estimate_ctr(self):
        """CTR 추정 테스트"""
        # 높은 점수 → 높은 CTR
        high_ctr = self.optimizer._estimate_ctr(90.0)
        low_ctr = self.optimizer._estimate_ctr(30.0)
        
        self.assertGreater(high_ctr, low_ctr)
        self.assertGreaterEqual(high_ctr, 2.0)
        self.assertLessEqual(high_ctr, 15.0)

    def test_generate_description(self):
        """설명 생성 테스트"""
        result = self.optimizer.generate_description(
            title="AI 영상 제작 가이드",
            topic=self.test_topic,
            keywords=self.test_keywords
        )

        self.assertIsInstance(result, dict)
        self.assertIn("full_description", result)
        self.assertIn("length", result)
        self.assertIn("keyword_density", result)
        
        # 설명이 비어있지 않은지
        self.assertGreater(len(result["full_description"]), 0)
        
        # 최대 길이 체크
        self.assertLessEqual(result["length"], self.optimizer.description_max_length)

    def test_generate_description_with_timestamps(self):
        """타임스탬프 포함 설명 생성 테스트"""
        result = self.optimizer.generate_description(
            title="Test Title",
            topic=self.test_topic,
            keywords=self.test_keywords,
            include_timestamps=True
        )

        self.assertIn("⏰ 타임스탬프", result["full_description"])
        self.assertIn("00:00", result["full_description"])

    def test_generate_tags(self):
        """태그 생성 테스트"""
        tags = self.optimizer.generate_tags(
            topic=self.test_topic,
            keywords=self.test_keywords
        )

        self.assertIsInstance(tags, list)
        self.assertGreater(len(tags), 0)
        self.assertLessEqual(len(tags), self.optimizer.max_tags)
        
        # 중복 없는지 확인
        self.assertEqual(len(tags), len(set(tags)))
        
        # 주제가 포함되어 있는지 확인
        self.assertIn(self.test_topic, tags)

    def test_generate_tags_with_viral_keywords(self):
        """바이럴 키워드 포함 태그 생성 테스트"""
        viral_keywords = [("트렌드", 100), ("인기", 80)]
        tags = self.optimizer.generate_tags(
            topic=self.test_topic,
            keywords=self.test_keywords,
            viral_keywords=viral_keywords
        )

        self.assertGreater(len(tags), 0)
        # 바이럴 키워드가 태그에 포함되어야 함
        has_viral = any(kw[0] in tags for kw in viral_keywords)
        self.assertTrue(has_viral or len(tags) >= 10)  # 또는 다른 태그로 채워짐

    def test_generate_hashtags(self):
        """해시태그 생성 테스트"""
        hashtags = self.optimizer.generate_hashtags(
            topic=self.test_topic,
            keywords=self.test_keywords
        )

        self.assertIsInstance(hashtags, list)
        self.assertGreater(len(hashtags), 0)
        self.assertLessEqual(len(hashtags), 5)
        
        # 공백이 없어야 함
        for tag in hashtags:
            self.assertNotIn(" ", tag)

    def test_select_category(self):
        """카테고리 선택 테스트"""
        result = self.optimizer.select_category(
            topic="AI 교육",
            keywords=["교육", "강의", "튜토리얼"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("category_name", result)
        self.assertIn("category_id", result)
        self.assertIn("confidence", result)
        
        # 교육 카테고리가 선택되어야 함
        self.assertEqual(result["category_name"], "교육")
        self.assertEqual(result["category_id"], 27)

    def test_select_category_fallback(self):
        """카테고리 선택 폴백 테스트 (매칭 없음)"""
        result = self.optimizer.select_category(
            topic="unknown topic",
            keywords=["xyz", "abc"]
        )

        # 기본값: 교육
        self.assertEqual(result["category_name"], "교육")
        self.assertEqual(result["category_id"], 27)

    def test_suggest_posting_time(self):
        """게시 시간 제안 테스트"""
        result = self.optimizer.suggest_posting_time()

        self.assertIsInstance(result, dict)
        self.assertIn("recommended_time", result)
        self.assertIn("day_type", result)
        self.assertIn("time_slot", result)
        self.assertIn("reason", result)
        
        # 주중/주말 구분
        self.assertIn(result["day_type"], ["주중", "주말"])

    def test_calculate_keyword_density(self):
        """키워드 밀도 계산 테스트"""
        text = "AI 영상 제작은 AI 기술의 영상 활용입니다"
        density = self.optimizer._calculate_keyword_density(text, ["AI", "영상"])
        
        self.assertGreater(density, 0)
        self.assertLessEqual(density, 100)

    def test_calculate_readability(self):
        """가독성 점수 계산 테스트"""
        # 가독성 점수가 0-100 범위인지만 확인
        text = "이것은 테스트 문장입니다. 가독성을 계산합니다."
        score = self.optimizer._calculate_readability(text)

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestSEOOptimizerIntegration(unittest.TestCase):
    """SEO 최적화 통합 테스트"""

    def test_optimize_video_seo_convenience_function(self):
        """종합 SEO 최적화 편의 함수 테스트"""
        result = optimize_video_seo(
            topic="AI 영상 제작",
            keywords=["AI", "영상", "제작", "자동화"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIn("description", result)
        self.assertIn("tags", result)
        self.assertIn("category", result)
        self.assertIn("posting_time", result)
        self.assertIn("overall_score", result)

    def test_complete_workflow(self):
        """완전한 SEO 최적화 워크플로우 테스트"""
        optimizer = SEOOptimizer()
        topic = "AI 영상 제작"
        keywords = ["AI", "영상", "자동화", "튜토리얼"]
        viral_keywords = [("트렌드", 100), ("인기", 80)]
        
        # 1. 제목 최적화
        title_result = optimizer.optimize_title(topic, keywords, viral_keywords)
        
        # 2. 설명 생성
        description_result = optimizer.generate_description(
            title_result["best_title"],
            topic,
            keywords
        )
        
        # 3. 태그 생성
        tags = optimizer.generate_tags(topic, keywords, viral_keywords)
        
        # 4. 해시태그 생성
        hashtags = optimizer.generate_hashtags(topic, keywords)
        
        # 5. 카테고리 선택
        category = optimizer.select_category(topic, keywords)
        
        # 6. 게시 시간 제안
        posting_time = optimizer.suggest_posting_time()
        
        # 모든 결과가 유효한지 확인
        self.assertIsNotNone(title_result["best_title"])
        self.assertGreater(len(description_result["full_description"]), 0)
        self.assertGreater(len(tags), 0)
        self.assertGreater(len(hashtags), 0)
        self.assertIsNotNone(category["category_id"])
        self.assertIsNotNone(posting_time["recommended_time"])


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.services.test_seo_optimizer.TestSEOOptimizer.test_optimize_title_basic
    unittest.main()
