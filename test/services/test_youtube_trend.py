#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
유튜브 트렌드 분석 모듈 테스트
"""
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.youtube_trend import YouTubeTrendAnalyzer, analyze_youtube_trends


class TestYouTubeTrendAnalyzer(unittest.TestCase):
    """유튜브 트렌드 분석기 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.analyzer = YouTubeTrendAnalyzer()

    def test_initialization_without_api_key(self):
        """API 키 없이 초기화 테스트"""
        analyzer = YouTubeTrendAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.api_key, "")

    def test_initialization_with_api_key(self):
        """API 키로 초기화 테스트"""
        test_key = "test_api_key_123"
        analyzer = YouTubeTrendAnalyzer(api_key=test_key)
        self.assertEqual(analyzer.api_key, test_key)

    def test_extract_keywords_from_text(self):
        """텍스트에서 키워드 추출 테스트"""
        text = "이것은 테스트 텍스트입니다. 유튜브 트렌드 분석을 테스트합니다."
        keywords = self.analyzer._extract_keywords_from_text(text)

        self.assertIsInstance(keywords, list)
        self.assertTrue(all(len(kw) >= 2 for kw in keywords))
        self.assertIn("유튜브", keywords)
        self.assertIn("트렌드", keywords)

    def test_parse_duration(self):
        """ISO 8601 duration 파싱 테스트"""
        # 1시간 2분 30초
        duration1 = self.analyzer._parse_duration("PT1H2M30S")
        self.assertEqual(duration1, 3750)  # 3600 + 120 + 30

        # 5분
        duration2 = self.analyzer._parse_duration("PT5M")
        self.assertEqual(duration2, 300)

        # 45초
        duration3 = self.analyzer._parse_duration("PT45S")
        self.assertEqual(duration3, 45)

        # 잘못된 형식
        duration4 = self.analyzer._parse_duration("invalid")
        self.assertEqual(duration4, 0)

    def test_calculate_engagement_rate(self):
        """참여율 계산 테스트"""
        video = {
            "view_count": 1000,
            "like_count": 50,
            "comment_count": 20
        }
        rate = self.analyzer._calculate_engagement_rate(video)
        self.assertEqual(rate, 0.07)  # (50+20)/1000

        # 조회수 0인 경우
        video_no_views = {
            "view_count": 0,
            "like_count": 10,
            "comment_count": 5
        }
        rate_zero = self.analyzer._calculate_engagement_rate(video_no_views)
        self.assertEqual(rate_zero, 0.0)

    def test_get_korean_stopwords(self):
        """한국어 불용어 목록 테스트"""
        stopwords = self.analyzer._get_korean_stopwords()

        self.assertIsInstance(stopwords, set)
        self.assertIn("그리고", stopwords)
        self.assertIn("하지만", stopwords)
        self.assertIn("the", stopwords)
        self.assertIn("and", stopwords)

    def test_extract_viral_keywords(self):
        """바이럴 키워드 추출 테스트"""
        test_videos = [
            {
                "title": "맛집 추천 서울 강남 맛집 베스트",
                "tags": ["맛집", "서울", "강남", "추천"]
            },
            {
                "title": "강남 맛집 탐방 서울 여행",
                "tags": ["강남", "맛집", "여행"]
            },
            {
                "title": "서울 핫플 추천",
                "tags": ["서울", "추천", "핫플"]
            }
        ]

        keywords = self.analyzer.extract_viral_keywords(test_videos, top_n=5)

        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) > 0)
        # 가장 많이 등장하는 키워드 확인
        top_keyword = keywords[0][0] if keywords else None
        self.assertIn(top_keyword, ["맛집", "서울", "강남", "추천"])

    def test_analyze_optimal_duration(self):
        """최적 영상 길이 분석 테스트"""
        test_videos = [
            {
                "duration": "PT1M30S",  # 90초
                "view_count": 10000,
                "like_count": 500,
                "comment_count": 50
            },
            {
                "duration": "PT2M",  # 120초
                "view_count": 15000,
                "like_count": 800,
                "comment_count": 100
            },
            {
                "duration": "PT1M",  # 60초
                "view_count": 8000,
                "like_count": 300,
                "comment_count": 30
            }
        ]

        analysis = self.analyzer.analyze_optimal_duration(test_videos)

        self.assertIsInstance(analysis, dict)
        self.assertIn("average_seconds", analysis)
        self.assertIn("recommended_min_seconds", analysis)
        self.assertIn("recommended_max_seconds", analysis)
        self.assertGreater(analysis["average_seconds"], 0)

    def test_generate_title_suggestions(self):
        """제목 제안 생성 테스트"""
        topic = "프로그래밍"
        viral_keywords = [("파이썬", 10), ("코딩", 8), ("개발", 7)]
        title_patterns = {"avg_length": 50}

        suggestions = self.analyzer._generate_title_suggestions(
            topic,
            viral_keywords,
            title_patterns
        )

        self.assertIsInstance(suggestions, list)
        self.assertEqual(len(suggestions), 5)
        self.assertTrue(all(topic in s for s in suggestions))

    def test_generate_content_hooks(self):
        """콘텐츠 훅 생성 테스트"""
        viral_keywords = [("인기", 10), ("트렌드", 8)]

        hooks = self.analyzer._generate_content_hooks(viral_keywords)

        self.assertIsInstance(hooks, list)
        self.assertTrue(len(hooks) > 0)
        self.assertTrue(all(isinstance(h, str) for h in hooks))

    def test_generate_fallback_suggestions(self):
        """폴백 제안 생성 테스트"""
        topic = "여행"

        suggestions = self.analyzer._generate_fallback_suggestions(topic)

        self.assertIsInstance(suggestions, dict)
        self.assertIn("topic", suggestions)
        self.assertIn("viral_keywords", suggestions)
        self.assertIn("title_suggestions", suggestions)
        self.assertIn("content_hooks", suggestions)
        self.assertEqual(suggestions["topic"], topic)
        self.assertEqual(suggestions["metadata"]["mode"], "fallback")

    def test_analyze_youtube_trends_function(self):
        """편의 함수 테스트 (API 키 없음)"""
        result = analyze_youtube_trends("테스트 주제")

        self.assertIsInstance(result, dict)
        self.assertIn("topic", result)
        self.assertIn("viral_keywords", result)
        self.assertIn("title_suggestions", result)
        self.assertEqual(result["topic"], "테스트 주제")


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.services.test_youtube_trend.TestYouTubeTrendAnalyzer.test_parse_duration
    unittest.main()
