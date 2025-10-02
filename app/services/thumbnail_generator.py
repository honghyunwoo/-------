#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
썸네일 자동 생성 모듈

이 모듈은 유튜브 썸네일을 자동으로 생성합니다:
1. AI 기반 이미지 생성 (DALL-E, Stable Diffusion 등)
2. 템플릿 기반 썸네일 생성
3. 텍스트 오버레이 (제목, 키워드)
4. 클릭 유도 요소 추가 (화살표, 원, 강조 표시)
5. 얼굴/감정 표현 최적화
"""

import os
import io
import re
import base64
import requests
from typing import Optional, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from loguru import logger

from app.config import config


class ThumbnailGenerator:
    """썸네일 자동 생성기"""

    def __init__(self):
        """초기화"""
        self.output_size = (1280, 720)  # YouTube 권장 해상도
        self.font_sizes = {
            "title": 80,
            "subtitle": 50,
            "keyword": 40
        }

    def _get_korean_font(self, size: int):
        """
        한글 지원 폰트 로드 - Phase 1 Task 4 강화
        🚨 FIXED: 한글 폰트 완벽 적용 및 검증

        Args:
            size: 폰트 크기

        Returns:
            ImageFont 객체
        """
        # 🚨 FIXED: 한글 폰트 우선순위 재정렬 (한국어 최적화)
        korean_fonts = [
            # 1순위: 프로젝트 내 한글 폰트 (Charm-Bold.ttf)
            "resource/fonts/Charm-Bold.ttf",
            "resource/fonts/Charm-Regular.ttf",
            # 2순위: Windows 한글 폰트
            "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
            "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
            "C:/Windows/Fonts/NanumGothic.ttf", # 나눔고딕
            "C:/Windows/Fonts/gulim.ttc",       # 굴림
            "C:/Windows/Fonts/batang.ttc",      # 바탕
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux
        ]

        # 사용 가능한 폰트 찾기
        for font_path in korean_fonts:
            try:
                # 🚨 FIXED: 폰트 파일 존재 여부 먼저 확인
                if not os.path.exists(font_path):
                    logger.debug(f"Font file not found: {font_path}")
                    continue
                
                font = ImageFont.truetype(font_path, size)
                logger.info(f"✅ Loaded Korean font: {font_path}")
                
                # 🚨 FIXED: 폰트 로딩 검증 (한글 렌더링 테스트)
                if self._test_font_rendering(font, "안녕하세요"):
                    logger.info(f"🎯 Korean font validation successful: {font_path}")
                    return font
                else:
                    logger.warning(f"⚠️ Korean font validation failed: {font_path}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Failed to load font {font_path}: {e}")
                continue

        logger.error("❌ Korean font not found. Text may not display correctly.")
        return ImageFont.load_default()
    
    def _test_font_rendering(self, font, test_text: str) -> bool:
        """
        폰트의 한글 렌더링을 테스트합니다.
        
        Args:
            font: 테스트할 폰트 객체
            test_text: 테스트할 한글 텍스트
            
        Returns:
            bool: 한글 렌더링 성공 여부
        """
        try:
            # 임시 이미지 생성하여 폰트 렌더링 테스트
            test_img = Image.new('RGB', (100, 50), color='white')
            test_draw = ImageDraw.Draw(test_img)
            test_draw.text((10, 10), test_text, font=font, fill='black')
            
            # 렌더링된 텍스트가 비어있지 않은지 확인
            bbox = test_draw.textbbox((10, 10), test_text, font=font)
            if bbox[2] > bbox[0] and bbox[3] > bbox[1]:  # 너비와 높이가 0보다 큰지 확인
                return True
            else:
                return False
                
        except Exception as e:
            logger.debug(f"Font rendering test failed: {e}")
            return False

    def generate_from_template(
        self,
        title: str,
        background_color: Tuple[int, int, int] = (255, 100, 50),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        style: str = "gradient"
    ) -> Image.Image:
        """
        템플릿 기반 썸네일 생성

        Args:
            title: 썸네일 제목
            background_color: 배경색 (RGB)
            text_color: 텍스트 색상 (RGB)
            style: 스타일 ("gradient", "solid", "split")

        Returns:
            PIL Image 객체
        """
        # 캔버스 생성
        img = Image.new('RGB', self.output_size, background_color)
        draw = ImageDraw.Draw(img)

        # 배경 스타일 적용
        if style == "gradient":
            img = self._apply_gradient(img, background_color)
        elif style == "split":
            img = self._apply_split_background(img, background_color)

        # 테두리 효과
        img = self._add_border_effect(img)

        # 텍스트 추가
        img = self._add_text(
            img,
            title,
            text_color=text_color,
            position="center",
            max_width=1100
        )

        # 클릭 유도 요소 추가
        img = self._add_attention_elements(img)

        logger.info(f"Template thumbnail generated: {title[:30]}...")
        return img

    def generate_from_image(
        self,
        image_path: str,
        title: str,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        darken_background: bool = True
    ) -> Image.Image:
        """
        기존 이미지를 활용한 썸네일 생성

        Args:
            image_path: 배경 이미지 경로
            title: 썸네일 제목
            text_color: 텍스트 색상
            darken_background: 배경 어둡게 처리 여부

        Returns:
            PIL Image 객체
        """
        # 이미지 로드 및 리사이즈
        img = Image.open(image_path)
        img = img.resize(self.output_size, Image.Resampling.LANCZOS)

        # 배경 어둡게 처리
        if darken_background:
            img = self._darken_image(img, factor=0.6)

        # 텍스트 추가
        img = self._add_text(
            img,
            title,
            text_color=text_color,
            position="center",
            max_width=1100,
            add_shadow=True
        )

        # 클릭 유도 요소 추가
        img = self._add_attention_elements(img)

        logger.info(f"Image-based thumbnail generated: {title[:30]}...")
        return img

    def generate_viral_thumbnail(
        self,
        title: str,
        keywords: List[str],
        emotion: str = "surprised",
        background_image: Optional[str] = None
    ) -> Image.Image:
        """
        바이럴 최적화 썸네일 생성

        Args:
            title: 썸네일 제목
            keywords: 강조할 키워드 리스트
            emotion: 감정 표현 ("surprised", "excited", "curious")
            background_image: 배경 이미지 경로 (선택)

        Returns:
            PIL Image 객체
        """
        # 배경 생성
        if background_image and os.path.exists(background_image):
            img = Image.open(background_image)
            img = img.resize(self.output_size, Image.Resampling.LANCZOS)
            img = self._darken_image(img, factor=0.5)
        else:
            # 감정에 따른 색상 선택
            emotion_colors = {
                "surprised": (255, 50, 50),    # 빨강
                "excited": (255, 165, 0),      # 주황
                "curious": (138, 43, 226),     # 보라
                "happy": (255, 215, 0),        # 금색
                "serious": (25, 25, 112)       # 진한 파랑
            }
            bg_color = emotion_colors.get(emotion, (255, 100, 50))
            img = self._create_viral_background(bg_color)

        # 제목 텍스트 추가 (강조 스타일)
        img = self._add_viral_text(img, title, keywords)

        # 감정 이모지 추가
        img = self._add_emotion_emoji(img, emotion)

        # 강력한 클릭 유도 요소
        img = self._add_viral_elements(img)

        logger.info(f"Viral thumbnail generated: {title[:30]}...")
        return img

    def generate_with_ai(
        self,
        prompt: str,
        title: str,
        provider: str = "openai"
    ) -> Optional[Image.Image]:
        """
        AI를 활용한 썸네일 배경 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            title: 썸네일 제목
            provider: AI 제공업체 ("openai", "pollinations")

        Returns:
            PIL Image 객체 또는 None
        """
        try:
            if provider == "openai":
                return self._generate_with_dalle(prompt, title)
            elif provider == "pollinations":
                return self._generate_with_pollinations(prompt, title)
            else:
                logger.warning(f"Unknown AI provider: {provider}")
                return None
        except Exception as e:
            logger.error(f"AI thumbnail generation failed: {e}")
            return None

    def save_thumbnail(self, img: Image.Image, output_path: str) -> bool:
        """
        썸네일 저장

        Args:
            img: PIL Image 객체
            output_path: 저장 경로

        Returns:
            성공 여부
        """
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 고품질로 저장
            img.save(output_path, "JPEG", quality=95, optimize=True)
            logger.success(f"Thumbnail saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save thumbnail: {e}")
            return False

    # ========== 내부 헬퍼 함수 ==========

    def _apply_gradient(
        self,
        img: Image.Image,
        base_color: Tuple[int, int, int]
    ) -> Image.Image:
        """그라데이션 배경 적용"""
        width, height = img.size
        gradient = Image.new('RGB', (width, height), base_color)
        draw = ImageDraw.Draw(gradient)

        # 세로 그라데이션
        r, g, b = base_color
        for y in range(height):
            # 밝기 조정
            factor = y / height
            new_r = int(r * (1 - factor * 0.3))
            new_g = int(g * (1 - factor * 0.3))
            new_b = int(b * (1 - factor * 0.3))

            draw.line([(0, y), (width, y)], fill=(new_r, new_g, new_b))

        return gradient

    def _apply_split_background(
        self,
        img: Image.Image,
        base_color: Tuple[int, int, int]
    ) -> Image.Image:
        """분할 배경 적용 (좌우 또는 상하)"""
        width, height = img.size
        draw = ImageDraw.Draw(img)

        r, g, b = base_color

        # 왼쪽 절반
        left_color = (r, g, b)
        draw.rectangle([(0, 0), (width // 2, height)], fill=left_color)

        # 오른쪽 절반 (약간 어둡게)
        right_color = (int(r * 0.7), int(g * 0.7), int(b * 0.7))
        draw.rectangle([(width // 2, 0), (width, height)], fill=right_color)

        return img

    def _add_border_effect(self, img: Image.Image) -> Image.Image:
        """테두리 효과 추가"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 두꺼운 흰색 테두리
        border_width = 15
        border_color = (255, 255, 255)

        for i in range(border_width):
            draw.rectangle(
                [(i, i), (width - i - 1, height - i - 1)],
                outline=border_color,
                width=1
            )

        return img

    def _add_text(
        self,
        img: Image.Image,
        text: str,
        text_color: Tuple[int, int, int],
        position: str = "center",
        max_width: int = 1100,
        add_shadow: bool = True
    ) -> Image.Image:
        """텍스트 추가"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 폰트 로드 (한글 지원 폰트 사용)
        font = self._get_korean_font(self.font_sizes["title"])

        # 텍스트를 여러 줄로 분할
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # 텍스트 위치 계산
        line_height = self.font_sizes["title"] + 20
        total_height = len(lines) * line_height

        if position == "center":
            y = (height - total_height) // 2
        elif position == "top":
            y = 100
        else:  # bottom
            y = height - total_height - 100

        # 각 줄 그리기
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2

            # 그림자 효과
            if add_shadow:
                shadow_offset = 5
                draw.text(
                    (x + shadow_offset, y + shadow_offset),
                    line,
                    fill=(0, 0, 0),
                    font=font
                )

            # 텍스트
            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height

        return img

    def _add_attention_elements(self, img: Image.Image) -> Image.Image:
        """클릭 유도 요소 추가 (화살표, 원 등)"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 오른쪽 하단에 화살표
        arrow_color = (255, 255, 0)  # 노랑
        arrow_points = [
            (width - 150, height - 100),
            (width - 50, height - 100),
            (width - 50, height - 150),
            (width - 20, height - 75),
            (width - 50, height),
            (width - 50, height - 50),
            (width - 150, height - 50)
        ]

        draw.polygon(arrow_points, fill=arrow_color, outline=(255, 215, 0))

        return img

    def _darken_image(self, img: Image.Image, factor: float = 0.6) -> Image.Image:
        """이미지 어둡게 처리"""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def _create_viral_background(
        self,
        base_color: Tuple[int, int, int]
    ) -> Image.Image:
        """바이럴 최적화 배경 생성"""
        img = Image.new('RGB', self.output_size, base_color)

        # 강렬한 그라데이션 적용
        img = self._apply_gradient(img, base_color)

        # 노이즈 효과로 질감 추가
        img = self._add_texture(img)

        return img

    def _add_texture(self, img: Image.Image) -> Image.Image:
        """텍스처 추가"""
        # 미세한 블러로 부드러운 효과
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        return img

    def _add_viral_text(
        self,
        img: Image.Image,
        title: str,
        keywords: List[str]
    ) -> Image.Image:
        """바이럴 스타일 텍스트 추가"""
        # 제목 추가 (강조 스타일)
        img = self._add_text(
            img,
            title.upper(),  # 대문자로 강조
            text_color=(255, 255, 255),
            position="center",
            max_width=1100,
            add_shadow=True
        )

        # 키워드 강조
        if keywords:
            draw = ImageDraw.Draw(img)
            width, height = img.size

            keyword_font = self._get_korean_font(self.font_sizes["keyword"])

            # 상단에 키워드 배치
            keyword_text = f"🔥 {keywords[0]}" if keywords else ""
            bbox = draw.textbbox((0, 0), keyword_text, font=keyword_font)
            kw_width = bbox[2] - bbox[0]
            kw_x = (width - kw_width) // 2
            kw_y = 50

            # 배경 박스
            padding = 20
            draw.rectangle(
                [
                    (kw_x - padding, kw_y - padding),
                    (kw_x + kw_width + padding, kw_y + self.font_sizes["keyword"] + padding)
                ],
                fill=(255, 215, 0, 200)
            )

            # 키워드 텍스트
            draw.text((kw_x, kw_y), keyword_text, fill=(0, 0, 0), font=keyword_font)

        return img

    def _add_emotion_emoji(self, img: Image.Image, emotion: str) -> Image.Image:
        """감정 이모지 추가"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 감정별 이모지
        emojis = {
            "surprised": "😱",
            "excited": "🤩",
            "curious": "🤔",
            "happy": "😊",
            "serious": "🧐"
        }

        emoji = emojis.get(emotion, "😮")

        try:
            emoji_font = ImageFont.truetype("seguiemj.ttf", 150)  # Windows 이모지 폰트
        except:
            # 이모지 폰트 없으면 한글 폰트로 대체
            emoji_font = self._get_korean_font(150)

        # 왼쪽 상단에 배치
        draw.text((50, 50), emoji, fill=(255, 255, 255), font=emoji_font)

        return img

    def _add_viral_elements(self, img: Image.Image) -> Image.Image:
        """강력한 클릭 유도 요소 추가"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 1. 오른쪽 하단 화살표 (더 크고 강렬하게)
        arrow_color = (255, 255, 0)
        arrow_size = 200
        arrow_x = width - arrow_size - 30
        arrow_y = height - arrow_size - 30

        # 화살표 그리기
        draw.ellipse(
            [(arrow_x, arrow_y), (arrow_x + arrow_size, arrow_y + arrow_size)],
            fill=arrow_color,
            outline=(255, 0, 0),
            width=5
        )

        # 2. 왼쪽 하단에 "클릭!" 텍스트
        cta_font = self._get_korean_font(60)

        cta_text = "👆 CLICK!"
        draw.text((50, height - 100), cta_text, fill=(255, 255, 0), font=cta_font)

        return img

    def _generate_with_dalle(self, prompt: str, title: str) -> Optional[Image.Image]:
        """DALL-E로 이미지 생성"""
        try:
            from openai import OpenAI

            api_key = config.app.get("openai_api_key", "")
            if not api_key:
                logger.warning("OpenAI API key not configured")
                return None

            client = OpenAI(api_key=api_key)

            # 썸네일에 최적화된 프롬프트
            optimized_prompt = f"YouTube thumbnail style: {prompt}, vibrant colors, eye-catching, professional"

            response = client.images.generate(
                model="dall-e-3",
                prompt=optimized_prompt,
                size="1792x1024",
                quality="standard",
                n=1
            )

            # 이미지 다운로드
            image_url = response.data[0].url
            img_response = requests.get(image_url)
            img = Image.open(io.BytesIO(img_response.content))

            # 리사이즈
            img = img.resize(self.output_size, Image.Resampling.LANCZOS)

            # 텍스트 추가
            img = self._add_text(
                img,
                title,
                text_color=(255, 255, 255),
                position="center",
                add_shadow=True
            )

            logger.success("DALL-E thumbnail generated")
            return img

        except Exception as e:
            logger.error(f"DALL-E generation failed: {e}")
            return None

    def _generate_with_pollinations(
        self,
        prompt: str,
        title: str
    ) -> Optional[Image.Image]:
        """Pollinations AI로 이미지 생성 (무료)"""
        try:
            # Pollinations API 엔드포인트
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"

            params = {
                "width": 1280,
                "height": 720,
                "seed": -1,
                "nologo": "true"
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))

                # 텍스트 추가
                img = self._add_text(
                    img,
                    title,
                    text_color=(255, 255, 255),
                    position="center",
                    add_shadow=True
                )

                logger.success("Pollinations thumbnail generated")
                return img
            else:
                logger.error(f"Pollinations API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Pollinations generation failed: {e}")
            return None


# 편의 함수
def generate_thumbnail(
    title: str,
    style: str = "viral",
    keywords: List[str] = None,
    background_image: Optional[str] = None,
    output_path: Optional[str] = None
) -> Optional[Image.Image]:
    """
    썸네일 생성 편의 함수

    Args:
        title: 썸네일 제목
        style: 스타일 ("viral", "template", "image")
        keywords: 강조할 키워드
        background_image: 배경 이미지 경로
        output_path: 저장 경로

    Returns:
        PIL Image 객체
    """
    generator = ThumbnailGenerator()

    if style == "viral":
        img = generator.generate_viral_thumbnail(
            title=title,
            keywords=keywords or [],
            emotion="surprised"
        )
    elif style == "image" and background_image:
        img = generator.generate_from_image(
            image_path=background_image,
            title=title
        )
    else:  # template
        img = generator.generate_from_template(
            title=title,
            style="gradient"
        )

    if img and output_path:
        generator.save_thumbnail(img, output_path)

    return img
