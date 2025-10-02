#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
썸네일 생성기 모듈 테스트
"""
import unittest
import sys
from pathlib import Path
from PIL import Image

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.thumbnail_generator import ThumbnailGenerator


class TestThumbnailGenerator(unittest.TestCase):
    """썸네일 생성기 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.generator = ThumbnailGenerator()
        self.test_title = "이것은 테스트 제목입니다"

    def test_initialization(self):
        """초기화 테스트"""
        generator = ThumbnailGenerator()
        self.assertIsNotNone(generator)
        self.assertEqual(generator.output_size, (1280, 720))
        self.assertIn("title", generator.font_sizes)

    def test_generate_from_template_gradient(self):
        """템플릿 기반 그라데이션 썸네일 생성 테스트"""
        thumbnail = self.generator.generate_from_template(
            title=self.test_title,
            background_color=(255, 59, 48),
            text_color=(255, 255, 255),
            style="gradient"
        )
        
        self.assertIsInstance(thumbnail, Image.Image)
        self.assertEqual(thumbnail.size, (1280, 720))

    def test_generate_from_template_solid(self):
        """템플릿 기반 단색 썸네일 생성 테스트"""
        thumbnail = self.generator.generate_from_template(
            title=self.test_title,
            background_color=(52, 199, 89),
            text_color=(255, 255, 255),
            style="solid"
        )
        
        self.assertIsInstance(thumbnail, Image.Image)
        self.assertEqual(thumbnail.size, (1280, 720))

    def test_generate_from_template_split(self):
        """템플릿 기반 분할 썸네일 생성 테스트"""
        thumbnail = self.generator.generate_from_template(
            title=self.test_title,
            background_color=(255, 149, 0),
            text_color=(255, 255, 255),
            style="split"
        )
        
        self.assertIsInstance(thumbnail, Image.Image)
        self.assertEqual(thumbnail.size, (1280, 720))

    def test_generate_viral_thumbnail(self):
        """바이럴 썸네일 생성 테스트"""
        thumbnail = self.generator.generate_viral_thumbnail(
            title=self.test_title,
            keywords=["테스트", "키워드"],
            emotion="excited"
        )
        
        self.assertIsInstance(thumbnail, Image.Image)
        self.assertEqual(thumbnail.size, (1280, 720))

    def test_generate_viral_thumbnail_all_emotions(self):
        """모든 감정 타입 바이럴 썸네일 테스트"""
        emotions = ["excited", "curious", "happy", "shocked", "mysterious"]
        
        for emotion in emotions:
            thumbnail = self.generator.generate_viral_thumbnail(
                title=f"{emotion} 테스트",
                keywords=["테스트"],
                emotion=emotion
            )
            
            self.assertIsInstance(thumbnail, Image.Image)
            self.assertEqual(thumbnail.size, (1280, 720))

    def test_save_thumbnail(self):
        """썸네일 저장 테스트"""
        import tempfile
        import time
        
        thumbnail = self.generator.generate_from_template(
            title=self.test_title,
            background_color=(255, 59, 48),
            text_color=(255, 255, 255),
            style="gradient"
        )
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name
            
        success = self.generator.save_thumbnail(thumbnail, output_path)
        self.assertTrue(success)
        
        # 파일이 실제로 생성되었는지 확인
        self.assertTrue(Path(output_path).exists())
        
        # 저장된 이미지를 다시 열어서 확인
        loaded_img = Image.open(output_path)
        self.assertEqual(loaded_img.size, (1280, 720))
        loaded_img.close()
        
        # 파일 핸들 닫히기를 기다린 후 삭제
        time.sleep(0.1)
        try:
            Path(output_path).unlink()
        except PermissionError:
            pass  # Windows에서 파일이 잠긴 경우 무시

    def test_viral_thumbnail_with_keywords(self):
        """키워드가 포함된 바이럴 썸네일 테스트"""
        keywords = ["인기", "트렌드", "최신"]
        
        thumbnail = self.generator.generate_viral_thumbnail(
            title=self.test_title,
            keywords=keywords,
            emotion="curious"
        )
        
        self.assertIsInstance(thumbnail, Image.Image)
        self.assertEqual(thumbnail.size, (1280, 720))


class TestThumbnailGeneratorIntegration(unittest.TestCase):
    """썸네일 생성기 통합 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.generator = ThumbnailGenerator()

    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        import tempfile
        import time
        
        # 1. 바이럴 썸네일 생성
        thumbnail = self.generator.generate_viral_thumbnail(
            title="완전한 워크플로우 테스트",
            keywords=["테스트", "워크플로우"],
            emotion="excited"
        )
        
        # 2. 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name
            
        success = self.generator.save_thumbnail(thumbnail, output_path)
        
        # 3. 검증
        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())
        
        # 4. 저장된 이미지 검증
        loaded_img = Image.open(output_path)
        self.assertEqual(loaded_img.size, (1280, 720))
        loaded_img.close()
        
        # 5. 정리
        time.sleep(0.1)
        try:
            Path(output_path).unlink()
        except PermissionError:
            pass  # Windows에서 파일이 잠긴 경우 무시

    def test_multiple_styles_generation(self):
        """여러 스타일 동시 생성 테스트"""
        styles = ["gradient", "solid", "split"]
        
        for style in styles:
            thumbnail = self.generator.generate_from_template(
                title=f"{style} 스타일 테스트",
                background_color=(255, 59, 48),
                text_color=(255, 255, 255),
                style=style
            )
            
            self.assertIsInstance(thumbnail, Image.Image)
            self.assertEqual(thumbnail.size, (1280, 720))


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.services.test_thumbnail_generator.TestThumbnailGenerator.test_generate_viral_thumbnail
    unittest.main()
