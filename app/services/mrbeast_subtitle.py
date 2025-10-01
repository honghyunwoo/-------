#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MrBeast 스타일 자막 시스템

이 모듈은 MrBeast의 바이럴 영상 스타일 자막을 생성합니다:
1. 큰 폰트 크기 (화면의 20-30%)
2. 진한 외곽선 (검은색, 두께 8-12px)
3. 단어별 강조 (Karaoke 효과)
4. 감정 표현 (색상 변화, 크기 변화)
5. 화면 하단 중앙 배치
6. 애니메이션 효과 (페이드, 바운스, 스케일)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class SubtitleWord:
    """자막 단어 정보"""
    text: str
    start_time: float
    end_time: float
    emphasis: str = "normal"  # normal, strong, emotion
    color: str = "#FFFFFF"  # 흰색 기본


@dataclass
class SubtitleSegment:
    """자막 세그먼트 (문장 단위)"""
    words: List[SubtitleWord]
    start_time: float
    end_time: float
    style: str = "standard"  # standard, dramatic, energetic, calm


class MrBeastSubtitleGenerator:
    """MrBeast 스타일 자막 생성기"""

    def __init__(self):
        """초기화"""
        self.style_config = {
            "standard": {
                "font_size": 80,  # 큰 폰트
                "stroke_width": 10,  # 진한 외곽선
                "font_color": "#FFFFFF",  # 흰색
                "stroke_color": "#000000",  # 검은색 외곽선
                "position": "bottom",  # 하단 배치
                "padding": 100,  # 하단 여백
                "animation": "fade"  # 페이드 효과
            },
            "dramatic": {
                "font_size": 100,  # 더 큰 폰트
                "stroke_width": 12,
                "font_color": "#FFD700",  # 금색 (강조)
                "stroke_color": "#000000",
                "position": "bottom",
                "padding": 100,
                "animation": "bounce"  # 바운스 효과
            },
            "energetic": {
                "font_size": 90,
                "stroke_width": 11,
                "font_color": "#FF4444",  # 빨간색 (에너지)
                "stroke_color": "#000000",
                "position": "bottom",
                "padding": 100,
                "animation": "scale"  # 크기 변화
            },
            "calm": {
                "font_size": 70,
                "stroke_width": 8,
                "font_color": "#87CEEB",  # 하늘색 (차분함)
                "stroke_color": "#000000",
                "position": "bottom",
                "padding": 100,
                "animation": "fade"
            }
        }

        # 감정 키워드 (자동 스타일 감지)
        self.emotion_keywords = {
            "dramatic": ["충격", "놀라운", "믿을 수 없는", "완전히", "절대", 
                        "shocking", "amazing", "incredible", "totally", "absolutely"],
            "energetic": ["빠르게", "즉시", "지금", "바로", "최고", 
                         "fast", "now", "immediately", "best", "awesome"],
            "calm": ["천천히", "조용히", "부드럽게", "편안하게", 
                    "slowly", "quietly", "gently", "calmly"]
        }

        # 강조 단어 (크기/색상 강조)
        self.emphasis_keywords = [
            "중요", "핵심", "비밀", "진짜", "실제", "정말",
            "important", "key", "secret", "real", "actually", "really"
        ]

    def parse_srt(self, srt_content: str) -> List[SubtitleSegment]:
        """
        SRT 자막 파싱

        Args:
            srt_content: SRT 형식 자막 내용

        Returns:
            자막 세그먼트 리스트
        """
        segments = []
        
        # SRT 블록 분리 (빈 줄로 구분)
        blocks = re.split(r'\n\n+', srt_content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # 시간 정보 파싱
            time_line = lines[1]
            time_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                time_line
            )
            
            if not time_match:
                continue
            
            # 시작/종료 시간 계산 (초 단위)
            start_h, start_m, start_s, start_ms = map(int, time_match.groups()[:4])
            end_h, end_m, end_s, end_ms = map(int, time_match.groups()[4:])
            
            start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
            end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
            
            # 텍스트 추출
            text = ' '.join(lines[2:])
            
            # 단어 분리 및 시간 배분
            words = self._split_words_with_timing(text, start_time, end_time)
            
            # 스타일 자동 감지
            style = self._detect_style(text)
            
            segment = SubtitleSegment(
                words=words,
                start_time=start_time,
                end_time=end_time,
                style=style
            )
            segments.append(segment)
        
        logger.info(f"Parsed {len(segments)} subtitle segments")
        return segments

    def _split_words_with_timing(
        self,
        text: str,
        start_time: float,
        end_time: float
    ) -> List[SubtitleWord]:
        """
        텍스트를 단어로 분리하고 시간 배분

        Args:
            text: 텍스트
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            단어 리스트
        """
        # 단어 분리 (공백 기준)
        words_text = text.split()
        
        if not words_text:
            return []
        
        # 총 시간
        total_duration = end_time - start_time
        
        # 단어당 평균 시간
        word_duration = total_duration / len(words_text)
        
        words = []
        current_time = start_time
        
        for word_text in words_text:
            # 강조 여부 판단
            emphasis = self._detect_emphasis(word_text)
            
            # 색상 설정
            color = self._get_word_color(word_text, emphasis)
            
            word = SubtitleWord(
                text=word_text,
                start_time=current_time,
                end_time=current_time + word_duration,
                emphasis=emphasis,
                color=color
            )
            words.append(word)
            
            current_time += word_duration
        
        return words

    def _detect_style(self, text: str) -> str:
        """
        텍스트에서 스타일 자동 감지

        Args:
            text: 텍스트

        Returns:
            스타일 이름
        """
        text_lower = text.lower()
        
        # 각 감정의 키워드 매칭 수 계산
        style_scores = {}
        
        for style, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                style_scores[style] = score
        
        # 가장 높은 점수의 스타일 반환
        if style_scores:
            return max(style_scores, key=style_scores.get)
        
        return "standard"

    def _detect_emphasis(self, word: str) -> str:
        """
        단어 강조 여부 감지

        Args:
            word: 단어

        Returns:
            강조 레벨 (normal, strong, emotion)
        """
        word_lower = word.lower()
        
        # 감정 키워드 확인
        for style, keywords in self.emotion_keywords.items():
            if any(keyword in word_lower for keyword in keywords):
                return "emotion"
        
        # 강조 키워드 확인
        if any(keyword in word_lower for keyword in self.emphasis_keywords):
            return "strong"
        
        # 느낌표/물음표
        if '!' in word or '?' in word:
            return "emotion"
        
        # 대문자로만 구성 (영어)
        if word.isupper() and len(word) > 1:
            return "strong"
        
        return "normal"

    def _get_word_color(self, word: str, emphasis: str) -> str:
        """
        단어 색상 결정

        Args:
            word: 단어
            emphasis: 강조 레벨

        Returns:
            RGB 색상 코드
        """
        if emphasis == "emotion":
            return "#FFD700"  # 금색 (강한 강조)
        elif emphasis == "strong":
            return "#FF4444"  # 빨간색 (강조)
        else:
            return "#FFFFFF"  # 흰색 (기본)

    def generate_ass_subtitle(
        self,
        segments: List[SubtitleSegment],
        video_width: int = 1920,
        video_height: int = 1080
    ) -> str:
        """
        ASS (Advanced SubStation Alpha) 형식 자막 생성

        Args:
            segments: 자막 세그먼트 리스트
            video_width: 영상 너비
            video_height: 영상 높이

        Returns:
            ASS 형식 자막 문자열
        """
        # ASS 헤더
        ass_content = f"""[Script Info]
Title: MrBeast Style Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        
        # 스타일 정의
        for style_name, config in self.style_config.items():
            # ASS 색상 형식: &HAABBGGRR (알파, 파랑, 초록, 빨강)
            font_color = self._hex_to_ass_color(config["font_color"])
            stroke_color = self._hex_to_ass_color(config["stroke_color"])
            
            ass_content += f"""Style: {style_name}, Arial, {config['font_size']}, {font_color}, {font_color}, {stroke_color}, &H00000000, -1, 0, 0, 0, 100, 100, 0, 0, 1, {config['stroke_width']}, 0, 2, 10, 10, {config['padding']}, 1
"""
        
        # 이벤트 섹션
        ass_content += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # 각 세그먼트를 ASS 이벤트로 변환
        for segment in segments:
            for word in segment.words:
                # 시간 형식 변환 (HH:MM:SS.CC)
                start_time = self._seconds_to_ass_time(word.start_time)
                end_time = self._seconds_to_ass_time(word.end_time)
                
                # 단어별 색상 태그
                color_tag = self._hex_to_ass_color(word.color)
                
                # 애니메이션 태그
                animation = self._get_animation_tag(word.emphasis, segment.style)
                
                # ASS 이벤트 라인
                text = f"{{\\c{color_tag}}}{animation}{word.text}"
                
                ass_content += f"Dialogue: 0,{start_time},{end_time},{segment.style},,0,0,0,,{text}\n"
        
        logger.info(f"Generated ASS subtitle with {len(segments)} segments")
        return ass_content

    def _hex_to_ass_color(self, hex_color: str) -> str:
        """
        HEX 색상을 ASS 형식으로 변환

        Args:
            hex_color: #RRGGBB 형식

        Returns:
            &HAABBGGRR 형식
        """
        # '#' 제거
        hex_color = hex_color.lstrip('#')
        
        # RGB 추출
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # ASS 형식: &HAABBGGRR (알파는 00으로 고정)
        return f"&H00{b:02X}{g:02X}{r:02X}"

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """
        초를 ASS 시간 형식으로 변환

        Args:
            seconds: 초

        Returns:
            H:MM:SS.CC 형식
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def _get_animation_tag(self, emphasis: str, style: str) -> str:
        """
        강조 레벨과 스타일에 따른 애니메이션 태그 생성

        Args:
            emphasis: 강조 레벨
            style: 스타일

        Returns:
            ASS 애니메이션 태그
        """
        config = self.style_config.get(style, self.style_config["standard"])
        animation_type = config.get("animation", "fade")
        
        if emphasis == "emotion":
            # 강한 강조: 크기 확대 + 페이드
            return "{\\fscx120\\fscy120\\t(0,200,\\fscx100\\fscy100)}"
        elif emphasis == "strong":
            # 보통 강조: 약간 확대
            return "{\\fscx110\\fscy110\\t(0,150,\\fscx100\\fscy100)}"
        elif animation_type == "bounce":
            # 바운스 효과
            return "{\\move(0,10,0,-10)\\t(0,100,\\move(0,-10,0,10))}"
        elif animation_type == "scale":
            # 크기 변화
            return "{\\fscx90\\fscy90\\t(0,200,\\fscx100\\fscy100)}"
        else:
            # 기본 페이드
            return "{\\fad(100,100)}"


def generate_mrbeast_subtitle(
    srt_content: str,
    output_format: str = "ass",
    video_width: int = 1920,
    video_height: int = 1080
) -> str:
    """
    편의 함수: MrBeast 스타일 자막 생성

    Args:
        srt_content: SRT 형식 자막
        output_format: 출력 형식 (ass)
        video_width: 영상 너비
        video_height: 영상 높이

    Returns:
        변환된 자막 문자열
    """
    generator = MrBeastSubtitleGenerator()
    segments = generator.parse_srt(srt_content)
    
    if output_format == "ass":
        return generator.generate_ass_subtitle(segments, video_width, video_height)
    else:
        logger.warning(f"Unsupported format: {output_format}, using ASS")
        return generator.generate_ass_subtitle(segments, video_width, video_height)
