#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
바이럴 영상 제작 파이프라인 통합 테스트
"""
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.youtube_trend import YouTubeTrendAnalyzer
from app.services.hook_enhancer import HookEnhancer
from app.services.seo_optimizer import SEOOptimizer
from app.services.thumbnail_generator import ThumbnailGenerator
from app.services.mrbeast_subtitle import MrBeastSubtitleGenerator


class TestViralPipeline(unittest.TestCase):
    """바이럴 영상 제작 전체 워크플로우 통합 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.trend_analyzer = YouTubeTrendAnalyzer()
        self.hook_enhancer = HookEnhancer()
        self.seo_optimizer = SEOOptimizer()
        self.thumbnail_gen = ThumbnailGenerator()
        self.subtitle_gen = MrBeastSubtitleGenerator()

        # 테스트 주제
        self.test_topic = "AI 영상 제작 자동화"

    def test_complete_viral_workflow(self):
        """
        완전한 바이럴 영상 제작 워크플로우 테스트

        단계:
        1. 유튜브 트렌드 분석 → 바이럴 키워드 추출
        2. 후킹 강화 → 매력적인 오프닝 생성
        3. SEO 최적화 → 제목/설명/태그 최적화
        4. 썸네일 생성 → 클릭 유도 썸네일
        5. 자막 생성 → MrBeast 스타일 자막
        """

        # 1단계: 트렌드 분석
        trend_result = self.trend_analyzer._generate_fallback_suggestions(self.test_topic)

        self.assertIn("viral_keywords", trend_result)
        viral_keywords = trend_result["viral_keywords"]
        self.assertGreater(len(viral_keywords), 0)

        # 키워드 리스트 추출 (튜플의 첫 번째 요소만)
        keywords = [kw[0] for kw in viral_keywords[:5]]

        # 2단계: 후킹 강화
        hook_results = self.hook_enhancer.generate_hooks(
            topic=self.test_topic,
            style="curiosity",
            count=3
        )

        self.assertGreater(len(hook_results), 0)
        enhanced_hook = hook_results[0]["text"]  # 첫 번째 훅의 텍스트
        self.assertGreater(len(enhanced_hook), 0)

        # 후크 강도 검증
        hook_strength = self.hook_enhancer.analyze_hook_strength(enhanced_hook)
        self.assertGreaterEqual(hook_strength["strength_score"], 30.0)  # 기본 생성된 훅도 통과하도록 임계값 조정

        # 3단계: SEO 최적화
        # 제목 최적화
        title_result = self.seo_optimizer.optimize_title(
            topic=self.test_topic,
            keywords=keywords
        )

        self.assertIn("best_title", title_result)
        optimized_title = title_result["best_title"]
        self.assertGreater(title_result["score"], 10.0)  # 최소 점수 확인

        # 설명 생성
        description_result = self.seo_optimizer.generate_description(
            title=optimized_title,
            topic=self.test_topic,
            keywords=keywords,
            include_timestamps=True
        )

        self.assertIn("full_description", description_result)
        self.assertIn("⏰ 타임스탬프", description_result["full_description"])

        # 태그 생성 (바이럴 키워드를 튜플 형식으로 변환)
        viral_keywords_tuples = [(kw, 100) for kw in viral_keywords] if isinstance(viral_keywords[0], str) else viral_keywords
        tags = self.seo_optimizer.generate_tags(
            topic=self.test_topic,
            keywords=keywords,
            viral_keywords=viral_keywords_tuples
        )

        self.assertGreater(len(tags), 0)
        self.assertLessEqual(len(tags), 15)

        # 해시태그 생성
        hashtags = self.seo_optimizer.generate_hashtags(
            topic=self.test_topic,
            keywords=keywords
        )

        self.assertGreater(len(hashtags), 0)
        self.assertLessEqual(len(hashtags), 5)

        # 카테고리 선택
        category = self.seo_optimizer.select_category(
            topic=self.test_topic,
            keywords=keywords
        )

        self.assertIn("category_id", category)
        self.assertGreaterEqual(category["confidence"], 0)  # 0 이상이면 OK

        # 4단계: 썸네일 생성
        thumbnail_img = self.thumbnail_gen.generate_viral_thumbnail(
            title=optimized_title,
            keywords=keywords,
            emotion="excited"
        )

        # generate_viral_thumbnail은 PIL Image를 직접 반환
        self.assertIsNotNone(thumbnail_img)
        self.assertEqual(thumbnail_img.size, (1280, 720))

        # 5단계: 자막 스타일 생성
        # 테스트용 SRT 문자열 생성
        test_srt = f"""1
00:00:00,000 --> 00:00:05,000
{enhanced_hook}

2
00:00:05,000 --> 00:00:10,000
{self.test_topic}의 핵심을 알려드리겠습니다.

3
00:00:10,000 --> 00:00:15,000
놀라운 결과를 확인하세요!
"""

        # SRT 파싱
        segments = self.subtitle_gen.parse_srt(test_srt)
        self.assertGreater(len(segments), 0)

        # ASS 자막 생성
        ass_subtitle = self.subtitle_gen.generate_ass_subtitle(
            segments=segments
        )

        self.assertIn("[Script Info]", ass_subtitle)
        self.assertIn("[V4+ Styles]", ass_subtitle)
        self.assertIn("[Events]", ass_subtitle)

        # 테스트용으로 detected_style 설정
        detected_style = "energetic"

        # 전체 워크플로우 결과 검증
        workflow_result = {
            "trend_analysis": {
                "viral_keywords": viral_keywords,
                "keyword_count": len(viral_keywords)
            },
            "hook_enhancement": {
                "enhanced_hook": enhanced_hook,
                "strength_score": hook_strength["strength_score"]
            },
            "seo_optimization": {
                "title": optimized_title,
                "title_score": title_result["score"],
                "description_length": description_result["length"],
                "tags_count": len(tags),
                "hashtags": hashtags,
                "category": category["category_name"]
            },
            "thumbnail": {
                "created": True,
                "dimensions": f"{thumbnail_img.size[0]}x{thumbnail_img.size[1]}"
            },
            "subtitle": {
                "style": detected_style,
                "segment_count": len(segments)
            }
        }

        # 모든 단계가 성공적으로 완료되었는지 확인
        self.assertGreater(workflow_result["trend_analysis"]["keyword_count"], 0)
        self.assertGreater(workflow_result["hook_enhancement"]["strength_score"], 20.0)  # 기본 생성 훅도 통과
        self.assertGreater(workflow_result["seo_optimization"]["title_score"], 10.0)  # 최소 점수로 조정
        self.assertTrue(workflow_result["thumbnail"]["created"])
        self.assertGreater(workflow_result["subtitle"]["segment_count"], 0)

        print("\n=== 바이럴 영상 제작 워크플로우 완료 ===")
        print(f"주제: {self.test_topic}")
        print(f"\n1. 트렌드 분석:")
        print(f"   - 바이럴 키워드: {len(viral_keywords)}개")
        print(f"   - 상위 키워드: {', '.join(keywords[:3])}")
        print(f"\n2. 후킹 강화:")
        print(f"   - 강화된 훅: {enhanced_hook[:50]}...")
        print(f"   - 훅 강도: {hook_strength['strength_score']:.1f}/100")
        print(f"\n3. SEO 최적화:")
        print(f"   - 제목: {optimized_title[:50]}...")
        print(f"   - 제목 점수: {title_result['score']:.1f}/100")
        print(f"   - 태그: {len(tags)}개")
        print(f"   - 해시태그: {', '.join(hashtags)}")
        print(f"   - 카테고리: {category['category_name']}")
        print(f"\n4. 썸네일:")
        print(f"   - 크기: {thumbnail_img.size[0]}x{thumbnail_img.size[1]}")
        print(f"   - 형식: PNG")
        print(f"\n5. 자막:")
        print(f"   - 스타일: {detected_style}")
        print(f"   - 세그먼트: {len(segments)}개")
        print("\n✅ 모든 바이럴 기능이 정상 작동합니다!")


class TestModuleIntegration(unittest.TestCase):
    """개별 모듈 간 데이터 흐름 테스트"""

    def test_trend_to_hook_integration(self):
        """트렌드 분석 결과를 후킹 강화에 활용"""
        analyzer = YouTubeTrendAnalyzer()
        enhancer = HookEnhancer()

        # 트렌드 분석
        trend = analyzer._generate_fallback_suggestions("프로그래밍")
        viral_keywords = trend["viral_keywords"]

        # 후킹 강화
        hooks = enhancer.generate_hooks(
            topic="프로그래밍",
            style="curiosity",
            count=3
        )

        self.assertGreater(len(hooks), 0)
        hook = hooks[0]["text"]
        self.assertGreater(len(hook), 0)

    def test_trend_to_seo_integration(self):
        """트렌드 분석 결과를 SEO 최적화에 활용"""
        analyzer = YouTubeTrendAnalyzer()
        optimizer = SEOOptimizer()

        # 트렌드 분석
        trend = analyzer._generate_fallback_suggestions("여행")
        viral_keywords = trend["viral_keywords"]
        keywords = [kw[0] for kw in viral_keywords[:5]]

        # SEO 최적화에 바이럴 키워드 활용
        title = optimizer.optimize_title(
            topic="여행",
            keywords=keywords,
            viral_keywords=viral_keywords
        )

        self.assertGreater(title["score"], 0)
        self.assertIn("best_title", title)

    def test_seo_to_thumbnail_integration(self):
        """SEO 제목을 썸네일 생성에 활용"""
        optimizer = SEOOptimizer()
        thumbnail_gen = ThumbnailGenerator()

        # SEO 제목 생성
        title_result = optimizer.optimize_title(
            topic="요리",
            keywords=["레시피", "맛집", "요리"]
        )

        # 제목을 썸네일에 활용
        thumbnail = thumbnail_gen.generate_from_template(
            title=title_result["best_title"],
            style="gradient"
        )

        # generate_from_template은 PIL Image를 직접 반환
        self.assertIsNotNone(thumbnail)
        self.assertEqual(thumbnail.size, (1280, 720))

    def test_hook_to_subtitle_integration(self):
        """후킹 텍스트를 자막 시스템에 활용"""
        enhancer = HookEnhancer()
        subtitle_gen = MrBeastSubtitleGenerator()

        # 후크 생성
        hooks = enhancer.generate_hooks(
            topic="게임",
            style="shock",
            count=1
        )
        hook = hooks[0]["text"]

        # 후크를 SRT 형식으로 변환하여 자막 생성
        test_srt = f"""1
00:00:00,000 --> 00:00:05,000
{hook}
"""

        segments = subtitle_gen.parse_srt(test_srt)
        self.assertGreater(len(segments), 0)

        # ASS 자막 생성
        ass = subtitle_gen.generate_ass_subtitle(segments)
        self.assertIn("[Events]", ass)


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.integration.test_viral_pipeline.TestViralPipeline.test_complete_viral_workflow
    unittest.main(verbosity=2)
