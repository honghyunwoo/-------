#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MrBeast 스타일 자막 시스템 테스트
"""
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.mrbeast_subtitle import (
    MrBeastSubtitleGenerator,
    SubtitleWord,
    SubtitleSegment,
    generate_mrbeast_subtitle
)


class TestMrBeastSubtitleGenerator(unittest.TestCase):
    """MrBeast 스타일 자막 생성기 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.generator = MrBeastSubtitleGenerator()
        
        # 테스트용 SRT 샘플
        self.sample_srt = """1
00:00:00,000 --> 00:00:03,000
오늘은 AI로 영상을 만드는 방법을 알려드립니다

2
00:00:03,000 --> 00:00:06,000
정말 놀라운 결과를 보게 될 거예요!

3
00:00:06,000 --> 00:00:09,000
지금 바로 시작해볼까요?
"""

    def test_initialization(self):
        """초기화 테스트"""
        generator = MrBeastSubtitleGenerator()
        self.assertIsNotNone(generator)
        self.assertIn("standard", generator.style_config)
        self.assertIn("dramatic", generator.style_config)
        self.assertIn("energetic", generator.style_config)

    def test_style_config_structure(self):
        """스타일 설정 구조 테스트"""
        for style_name, config in self.generator.style_config.items():
            self.assertIn("font_size", config)
            self.assertIn("stroke_width", config)
            self.assertIn("font_color", config)
            self.assertIn("stroke_color", config)
            self.assertIn("position", config)
            self.assertIn("animation", config)
            
            # 폰트 크기 범위 확인 (50-150)
            self.assertGreaterEqual(config["font_size"], 50)
            self.assertLessEqual(config["font_size"], 150)

    def test_parse_srt_basic(self):
        """SRT 파싱 기본 테스트"""
        segments = self.generator.parse_srt(self.sample_srt)
        
        self.assertIsInstance(segments, list)
        self.assertEqual(len(segments), 3)
        
        # 첫 번째 세그먼트 검증
        first_segment = segments[0]
        self.assertIsInstance(first_segment, SubtitleSegment)
        self.assertGreater(len(first_segment.words), 0)
        self.assertEqual(first_segment.start_time, 0.0)
        self.assertEqual(first_segment.end_time, 3.0)

    def test_parse_srt_timing(self):
        """SRT 파싱 시간 정보 테스트"""
        segments = self.generator.parse_srt(self.sample_srt)
        
        # 시간이 순차적인지 확인
        for i in range(len(segments) - 1):
            self.assertLessEqual(
                segments[i].end_time,
                segments[i + 1].start_time + 0.1  # 약간의 오차 허용
            )

    def test_split_words_with_timing(self):
        """단어 분리 및 시간 배분 테스트"""
        text = "오늘은 AI로 영상을 만듭니다"
        start_time = 0.0
        end_time = 3.0
        
        words = self.generator._split_words_with_timing(text, start_time, end_time)
        
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 0)
        
        # 각 단어가 SubtitleWord 인스턴스인지 확인
        for word in words:
            self.assertIsInstance(word, SubtitleWord)
            self.assertIsInstance(word.text, str)
            self.assertGreaterEqual(word.start_time, start_time)
            self.assertLessEqual(word.end_time, end_time)

    def test_detect_style_dramatic(self):
        """극적 스타일 감지 테스트"""
        dramatic_text = "이것은 정말 충격적이고 놀라운 결과입니다!"
        style = self.generator._detect_style(dramatic_text)
        
        self.assertEqual(style, "dramatic")

    def test_detect_style_energetic(self):
        """에너지 스타일 감지 테스트"""
        energetic_text = "지금 바로 빠르게 시작해봅시다!"
        style = self.generator._detect_style(energetic_text)
        
        self.assertEqual(style, "energetic")

    def test_detect_style_calm(self):
        """차분한 스타일 감지 테스트"""
        calm_text = "천천히 부드럽게 진행해봅시다"
        style = self.generator._detect_style(calm_text)
        
        self.assertEqual(style, "calm")

    def test_detect_style_standard(self):
        """표준 스타일 감지 테스트 (감정 키워드 없음)"""
        standard_text = "이것은 일반적인 문장입니다"
        style = self.generator._detect_style(standard_text)
        
        self.assertEqual(style, "standard")

    def test_detect_emphasis_emotion(self):
        """감정 강조 감지 테스트"""
        emotion_word = "충격적인!"
        emphasis = self.generator._detect_emphasis(emotion_word)
        
        self.assertEqual(emphasis, "emotion")

    def test_detect_emphasis_strong(self):
        """강한 강조 감지 테스트"""
        strong_word = "중요한"
        emphasis = self.generator._detect_emphasis(strong_word)
        
        self.assertEqual(emphasis, "strong")

    def test_detect_emphasis_normal(self):
        """일반 강조 감지 테스트"""
        normal_word = "일반적인"
        emphasis = self.generator._detect_emphasis(normal_word)
        
        self.assertEqual(emphasis, "normal")

    def test_get_word_color(self):
        """단어 색상 결정 테스트"""
        # 감정 강조
        emotion_color = self.generator._get_word_color("test", "emotion")
        self.assertEqual(emotion_color, "#FFD700")  # 금색
        
        # 강한 강조
        strong_color = self.generator._get_word_color("test", "strong")
        self.assertEqual(strong_color, "#FF4444")  # 빨간색
        
        # 일반
        normal_color = self.generator._get_word_color("test", "normal")
        self.assertEqual(normal_color, "#FFFFFF")  # 흰색

    def test_hex_to_ass_color(self):
        """HEX 색상 ASS 형식 변환 테스트"""
        # 흰색
        white_ass = self.generator._hex_to_ass_color("#FFFFFF")
        self.assertEqual(white_ass, "&H00FFFFFF")
        
        # 빨간색
        red_ass = self.generator._hex_to_ass_color("#FF0000")
        self.assertEqual(red_ass, "&H000000FF")
        
        # 검은색
        black_ass = self.generator._hex_to_ass_color("#000000")
        self.assertEqual(black_ass, "&H00000000")

    def test_seconds_to_ass_time(self):
        """초를 ASS 시간 형식으로 변환 테스트"""
        # 0초
        time_0 = self.generator._seconds_to_ass_time(0.0)
        self.assertEqual(time_0, "0:00:00.00")
        
        # 3.5초
        time_3_5 = self.generator._seconds_to_ass_time(3.5)
        self.assertEqual(time_3_5, "0:00:03.50")
        
        # 65.25초 (1분 5.25초)
        time_65_25 = self.generator._seconds_to_ass_time(65.25)
        self.assertEqual(time_65_25, "0:01:05.25")
        
        # 3665초 (1시간 1분 5초)
        time_3665 = self.generator._seconds_to_ass_time(3665.0)
        self.assertEqual(time_3665, "1:01:05.00")

    def test_get_animation_tag(self):
        """애니메이션 태그 생성 테스트"""
        # 감정 강조
        emotion_tag = self.generator._get_animation_tag("emotion", "standard")
        self.assertIn("fscx120", emotion_tag)  # 크기 확대
        
        # 강한 강조
        strong_tag = self.generator._get_animation_tag("strong", "standard")
        self.assertIn("fscx110", strong_tag)
        
        # 일반
        normal_tag = self.generator._get_animation_tag("normal", "standard")
        self.assertIsInstance(normal_tag, str)

    def test_generate_ass_subtitle_basic(self):
        """ASS 자막 생성 기본 테스트"""
        segments = self.generator.parse_srt(self.sample_srt)
        ass_content = self.generator.generate_ass_subtitle(segments)
        
        self.assertIsInstance(ass_content, str)
        self.assertIn("[Script Info]", ass_content)
        self.assertIn("[V4+ Styles]", ass_content)
        self.assertIn("[Events]", ass_content)
        self.assertIn("Dialogue:", ass_content)

    def test_generate_ass_subtitle_styles(self):
        """ASS 자막 스타일 포함 테스트"""
        segments = self.generator.parse_srt(self.sample_srt)
        ass_content = self.generator.generate_ass_subtitle(segments)
        
        # 모든 스타일이 포함되어 있는지 확인
        for style_name in self.generator.style_config.keys():
            self.assertIn(f"Style: {style_name}", ass_content)

    def test_generate_ass_subtitle_resolution(self):
        """ASS 자막 해상도 설정 테스트"""
        segments = self.generator.parse_srt(self.sample_srt)
        ass_content = self.generator.generate_ass_subtitle(
            segments,
            video_width=1280,
            video_height=720
        )
        
        self.assertIn("PlayResX: 1280", ass_content)
        self.assertIn("PlayResY: 720", ass_content)


class TestMrBeastSubtitleIntegration(unittest.TestCase):
    """MrBeast 자막 통합 테스트"""

    def test_generate_mrbeast_subtitle_convenience_function(self):
        """편의 함수 테스트"""
        sample_srt = """1
00:00:00,000 --> 00:00:03,000
테스트 자막입니다
"""
        
        result = generate_mrbeast_subtitle(sample_srt)
        
        self.assertIsInstance(result, str)
        self.assertIn("[Script Info]", result)
        self.assertIn("Dialogue:", result)

    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        generator = MrBeastSubtitleGenerator()
        
        # 1. SRT 파싱
        sample_srt = """1
00:00:00,000 --> 00:00:02,000
놀라운 AI 기술!

2
00:00:02,000 --> 00:00:04,000
지금 바로 시작하세요
"""
        segments = generator.parse_srt(sample_srt)
        
        # 2. ASS 생성
        ass_content = generator.generate_ass_subtitle(segments, 1920, 1080)
        
        # 3. 검증
        self.assertEqual(len(segments), 2)
        self.assertIn("[Script Info]", ass_content)
        self.assertIn("Dialogue:", ass_content)
        
        # 스타일 자동 감지 확인
        self.assertIn(segments[0].style, ["dramatic", "energetic", "standard"])


if __name__ == "__main__":
    # 개별 테스트 실행 예시:
    # python -m unittest test.services.test_mrbeast_subtitle.TestMrBeastSubtitleGenerator.test_parse_srt_basic
    unittest.main()
