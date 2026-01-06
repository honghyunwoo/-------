"""
썸네일 생성 모듈
영상에서 프레임 추출 + 텍스트 오버레이로 썸네일 생성
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# FFmpeg 경로 (imageio_ffmpeg 사용)
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_PATH = "ffmpeg"


class ThumbnailGenerator:
    """텍스트 오버레이 썸네일 생성기"""

    def __init__(
        self,
        font_path: str = "C:\\Windows\\Fonts\\malgunbd.ttf",
        width: int = 1080,
        height: int = 1920
    ):
        self.font_path = font_path
        self.width = width
        self.height = height

    def generate(
        self,
        video_path: Path,
        output_path: Path,
        hook_text: str,
        timestamp: float = 0.5  # 자막 나오기 전 시점
    ) -> Path:
        """
        썸네일 생성

        Args:
            video_path: 영상 파일 경로
            output_path: 출력 썸네일 경로
            hook_text: 표시할 훅 문장 (s1_hook)
            timestamp: 프레임 추출 시점 (초)

        Returns:
            생성된 썸네일 경로
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 영상에서 프레임 추출
        temp_frame = output_path.parent / "_temp_frame.png"
        self._extract_frame(video_path, temp_frame, timestamp)

        # 2. 텍스트 오버레이 적용
        self._apply_overlay(temp_frame, output_path, hook_text)

        # 3. 임시 파일 삭제
        if temp_frame.exists():
            temp_frame.unlink()

        return output_path

    def _extract_frame(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float
    ):
        """FFmpeg로 프레임 추출"""
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]

        subprocess.run(
            cmd,
            capture_output=True,
            check=True
        )

    def _apply_overlay(
        self,
        frame_path: Path,
        output_path: Path,
        hook_text: str
    ):
        """Pillow로 텍스트 오버레이 - 깔끔한 중앙 배치"""
        # 프레임 로드
        img = Image.open(frame_path)
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # 1. 전체 어둡게 (가독성 향상)
        dark_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 100))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, dark_overlay)

        # 2. 상단/하단 그라데이션 (더 강하게)
        gradient = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw_grad = ImageDraw.Draw(gradient)

        for i in range(500):
            alpha = int(200 * (1 - i / 500))
            draw_grad.line([(0, i), (self.width, i)], fill=(0, 0, 0, alpha))
            draw_grad.line(
                [(0, self.height - i - 1), (self.width, self.height - i - 1)],
                fill=(0, 0, 0, alpha)
            )
        img = Image.alpha_composite(img, gradient)

        # 3. 텍스트 준비
        draw = ImageDraw.Draw(img)

        # 화면 너비에 맞는 폰트 크기 계산
        padding = 80  # 좌우 여백
        max_text_width = self.width - (padding * 2)

        # 줄바꿈 처리 (더 긴 줄 허용)
        lines = self._wrap_text_smart(hook_text, max_width=max_text_width)

        # 폰트 크기 동적 계산
        font_size = self._calculate_font_size(lines, max_text_width)
        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            font = ImageFont.load_default()

        # 4. 텍스트 배경 박스 (반투명)
        line_height = font_size + 24
        total_text_height = len(lines) * line_height
        box_padding = 40
        box_top = (self.height - total_text_height) // 2 - box_padding
        box_bottom = box_top + total_text_height + (box_padding * 2)

        # 둥근 모서리 배경
        box_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        box_draw = ImageDraw.Draw(box_overlay)
        box_draw.rounded_rectangle(
            [(padding - 20, box_top), (self.width - padding + 20, box_bottom)],
            radius=20,
            fill=(0, 0, 0, 140)
        )
        img = Image.alpha_composite(img, box_overlay)

        # 5. 텍스트 그리기
        draw = ImageDraw.Draw(img)
        y_start = (self.height - total_text_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            y = y_start + i * line_height

            # 텍스트 그림자
            for offset in [(3, 3), (2, 2), (1, 1)]:
                draw.text(
                    (x + offset[0], y + offset[1]),
                    line,
                    font=font,
                    fill=(0, 0, 0, 180)
                )

            # 텍스트 본체 (흰색)
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

        # 6. PNG로 저장
        img = img.convert('RGB')
        img.save(output_path, 'PNG', quality=95)

    def _wrap_text_smart(self, text: str, max_width: int) -> list:
        """화면 너비에 맞게 스마트 줄바꿈"""
        # 문장 부호로 먼저 시도
        if ',' in text:
            parts = [p.strip() for p in text.split(',') if p.strip()]
            if len(parts) <= 3:
                return parts

        # 단어 단위로 분리
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            # 대략적인 글자 수로 판단 (한글 기준)
            if len(test_line) <= 16:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines[:4]  # 최대 4줄

    def _calculate_font_size(self, lines: list, max_width: int) -> int:
        """텍스트가 화면에 맞도록 폰트 크기 계산"""
        max_line_len = max(len(line) for line in lines) if lines else 10

        # 글자 수에 따른 폰트 크기 조정
        if max_line_len <= 8:
            return 80
        elif max_line_len <= 12:
            return 64
        elif max_line_len <= 16:
            return 52
        else:
            return 44

    def _wrap_text(self, text: str, max_chars: int = 12) -> list:
        """텍스트를 max_chars 기준으로 줄바꿈"""
        # 문장 부호로 먼저 분리
        if ',' in text:
            parts = text.split(',')
            return [p.strip() for p in parts if p.strip()]

        # 길이 기준 분리
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if len(test_line) <= max_chars:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # 최대 3줄
        return lines[:3]

    def generate_from_script(
        self,
        video_path: Path,
        script_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """script.json에서 훅 문장을 읽어 썸네일 생성"""
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        hook_text = script.get('s1_hook', '')

        if output_path is None:
            output_path = video_path.parent / "thumbnail.png"

        return self.generate(video_path, output_path, hook_text)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python thumbnail_generator.py <project_folder>")
        print("Example: python thumbnail_generator.py output/20260106_집중_미루기_01")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    video_path = project_dir / "video.mp4"
    script_path = project_dir / "script.json"
    output_path = project_dir / "thumbnail.png"

    if not video_path.exists():
        print(f"[ERROR] Video not found: {video_path}")
        sys.exit(1)

    generator = ThumbnailGenerator()
    result = generator.generate_from_script(video_path, script_path, output_path)
    print(f"[OK] Thumbnail generated: {result}")
