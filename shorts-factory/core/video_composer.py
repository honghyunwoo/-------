"""
영상 합성 모듈
오디오 + B-roll + 자막 → 최종 영상
"""

import textwrap
import logging
from multiprocessing import cpu_count
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# 최적 스레드 수 계산 (CPU 코어 - 1, 최소 2)
OPTIMAL_THREADS = max(2, cpu_count() - 1)

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    ColorClip
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, MultiplyVolume
# MoviePy 2.x uses clip.resized() and clip.cropped() methods
# MoviePy 2.x uses with_effects([effect]) for audio effects

from .broll_selector import BrollClip
from .subtitle_generator import SubtitleEntry, SubtitleGenerator


# =============================================================================
# 시네마틱 효과 (AI Slop 회피)
# =============================================================================

def add_vignette(clip, intensity: float = 0.3):
    """
    비네팅 효과 - 화면 가장자리 어둡게
    스토아 철학의 무겁고 진지한 분위기에 최적

    Args:
        clip: VideoFileClip
        intensity: 0.0 (없음) ~ 1.0 (강함), 기본 0.3
    """
    def vignette_frame(frame):
        h, w = frame.shape[:2]
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2

        # 중앙에서의 거리 계산
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        dist_normalized = dist / max_dist

        # 비네팅 마스크 (중앙=1, 가장자리=1-intensity)
        mask = 1 - (dist_normalized * intensity)
        mask = np.clip(mask, 0, 1)

        # RGB 각 채널에 적용
        result = frame.astype(np.float32)
        for i in range(3):
            result[:, :, i] = result[:, :, i] * mask

        return result.astype(np.uint8)

    return clip.image_transform(vignette_frame)


def add_film_grain(clip, intensity: float = 0.03):
    """
    필름 그레인 효과 - 미세 노이즈로 디지털 매끄러움 제거
    AI 양산형 느낌을 지워주는 핵심 효과

    Args:
        clip: VideoFileClip
        intensity: 0.01 (미세) ~ 0.08 (강함), 기본 0.03
    """
    def grain_frame(frame):
        # Gaussian noise 추가
        noise = np.random.normal(0, intensity * 255, frame.shape)
        result = frame.astype(np.float32) + noise
        return np.clip(result, 0, 255).astype(np.uint8)

    return clip.image_transform(grain_frame)


def apply_color_grade(clip, preset: str = 'stoic_navy_gold'):
    """
    색 보정 프리셋 적용

    Args:
        clip: VideoFileClip
        preset: 'stoic_navy_gold', 'warm_sepia', 'cold_dramatic'
    """
    from moviepy.video import fx as vfx

    presets = {
        'stoic_navy_gold': {
            'saturation': 0.85,    # 채도 약간 낮춤
            'contrast': 1.12,      # 대비 높임
            'blue_tint': 0.05,     # 블루 틴트
        },
        'warm_sepia': {
            'saturation': 0.9,
            'contrast': 1.08,
            'red_tint': 0.08,
        },
        'cold_dramatic': {
            'saturation': 0.75,
            'contrast': 1.25,
            'blue_tint': 0.1,
        },
        'neutral_clean': {
            'saturation': 1.0,
            'contrast': 1.0,
        }
    }

    settings = presets.get(preset, presets['stoic_navy_gold'])

    def color_grade_frame(frame):
        result = frame.astype(np.float32)

        # 채도 조절 (HSV 변환 대신 간단한 방식)
        gray = np.mean(result, axis=2, keepdims=True)
        sat = settings.get('saturation', 1.0)
        result = gray + sat * (result - gray)

        # 대비 조절
        contrast = settings.get('contrast', 1.0)
        result = 128 + contrast * (result - 128)

        # 틴트 적용
        if 'blue_tint' in settings:
            result[:, :, 2] = result[:, :, 2] + settings['blue_tint'] * 50
        if 'red_tint' in settings:
            result[:, :, 0] = result[:, :, 0] + settings['red_tint'] * 50

        return np.clip(result, 0, 255).astype(np.uint8)

    return clip.image_transform(color_grade_frame)


# =============================================================================
# 영상 합성 설정
# =============================================================================

@dataclass
class CompositionConfig:
    """영상 합성 설정"""
    width: int = 1080
    height: int = 1920
    fps: int = 30
    codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "5M"

    # BGM
    bgm_volume: float = 0.2
    bgm_fade_in: float = 1.0
    bgm_fade_out: float = 2.0

    # 시네마틱 효과 (AI Slop 회피)
    enable_vignette: bool = True
    vignette_intensity: float = 0.25  # 0.0~1.0, 기본 약간 어둡게
    enable_film_grain: bool = True
    film_grain_intensity: float = 0.025  # 미세 노이즈
    color_grade_preset: str = "stoic_navy_gold"  # 프리셋 이름

    # 자막 (Stoic 스타일 - 금색)
    subtitle_font: str = "C:/Windows/Fonts/malgunbd.ttf"  # Bold 폰트
    subtitle_fontsize: int = 60  # 56 → 60 (더 크게)
    subtitle_color: str = "#FFD700"  # 금색 (gold)
    subtitle_stroke_color: str = "black"
    subtitle_stroke_width: int = 3
    subtitle_position: Tuple[str, str] = ("center", 0.8)
    subtitle_bottom_margin: int = 280  # YouTube UI 고려
    subtitle_text_margin: int = 20
    subtitle_wrap_width: int = 16  # 18 → 16 (더 짧은 줄, 가독성 향상)
    subtitle_max_width_ratio: float = 0.85  # 화면 너비의 85%

    # 하이라이트 (명언 강조)
    highlight_color: str = "#FFD700"  # 금색
    highlight_fontsize: int = 64


class VideoComposer:
    """영상 합성기"""

    def __init__(self, config: CompositionConfig = None):
        self.config = config or CompositionConfig()

    def compose(
        self,
        audio_path: Path,
        broll_clips: List[BrollClip],
        srt_path: Optional[Path] = None,
        bgm_path: Optional[Path] = None,
        output_path: Path = None
    ) -> Path:
        """영상 합성"""
        audio_path = Path(audio_path)
        output_path = Path(output_path) if output_path else audio_path.with_suffix('.mp4')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 오디오 로드
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        # 2. B-roll 연결 (각 클립은 _concatenate_broll에서 이미 리사이즈됨)
        if broll_clips:
            video = self._concatenate_broll(broll_clips, duration)
        else:
            # B-roll이 없으면 검은 배경
            video = ColorClip(
                size=(self.config.width, self.config.height),
                color=(0, 0, 0),
                duration=duration
            )

        # 2.5. 시네마틱 효과 적용 (AI Slop 회피)
        video = self._apply_cinematic_effects(video)

        # 3. 자막 오버레이
        if srt_path and Path(srt_path).exists():
            video = self._add_subtitles(video, srt_path)

        # 4. 오디오 합성
        if bgm_path and Path(bgm_path).exists():
            final_audio = self._mix_audio(audio, bgm_path, duration)
            video = video.with_audio(final_audio)
        else:
            video = video.with_audio(audio)

        # 6. 렌더링 (멀티스레드 최적화)
        # Windows 임시 파일 문제 해결: 명시적 temp_audiofile 경로 지정
        # AAC 코덱 사용 시 .m4a 확장자 필요
        temp_audio_path = output_path.parent / f"temp_audio_{output_path.stem}.m4a"

        try:
            video.write_videofile(
                str(output_path),
                fps=self.config.fps,
                codec=self.config.codec,
                audio_codec=self.config.audio_codec,
                bitrate=self.config.bitrate,
                threads=OPTIMAL_THREADS,
                preset='medium',
                temp_audiofile=str(temp_audio_path),
                remove_temp=True,
                logger=None  # 진행률 표시 끄기
            )
        finally:
            # 정리 (temp 파일이 남아있으면 삭제)
            if temp_audio_path.exists():
                try:
                    temp_audio_path.unlink()
                except:
                    pass

        # 정리
        video.close()
        audio.close()

        return output_path

    def _concatenate_broll(
        self,
        clips: List[BrollClip],
        target_duration: float,
        max_clip_duration: float = 6.0  # 클립당 최대 6초 (다양성 확보)
    ) -> VideoFileClip:
        """B-roll 클립 연결 - 각 클립을 9:16으로 리사이즈, 최대 길이 제한"""
        video_clips = []
        total_duration = 0.0

        for broll in clips:
            if not broll.path.exists():
                continue

            try:
                clip = VideoFileClip(str(broll.path))

                # 필요한 길이만큼만 사용
                remaining = target_duration - total_duration
                if remaining <= 0:
                    clip.close()
                    break

                # 클립 길이 제한 (다양성을 위해 최대 6초)
                use_duration = min(clip.duration, max_clip_duration, remaining)
                if clip.duration > use_duration:
                    clip = clip.subclipped(0, use_duration)

                # 각 클립을 풀스크린으로 리사이즈 (검은 띠 방지)
                clip = self._resize_to_vertical(clip)

                video_clips.append(clip)
                total_duration += clip.duration

            except Exception as e:
                logger.warning(f"클립 로드 실패: {broll.path} - {e}")
                continue

        if not video_clips:
            # 클립이 없으면 검은 배경
            return ColorClip(
                size=(self.config.width, self.config.height),
                color=(0, 0, 0),
                duration=target_duration
            )

        # 길이가 부족하면 마지막 클립 반복 (최대 10회 반복 제한)
        max_loops = 10
        loop_count = 0

        while total_duration < target_duration and video_clips and loop_count < max_loops:
            remaining = target_duration - total_duration
            if remaining <= 0:
                break

            last_clip = video_clips[-1]
            loop_clip = last_clip.subclipped(0, min(last_clip.duration, remaining))
            video_clips.append(loop_clip)
            total_duration += loop_clip.duration
            loop_count += 1

        return concatenate_videoclips(video_clips, method="compose")

    def _resize_to_vertical(self, video: VideoFileClip) -> VideoFileClip:
        """9:16 세로 비율로 리사이즈"""
        target_w = self.config.width
        target_h = self.config.height
        target_ratio = target_w / target_h

        w, h = video.size
        video_ratio = w / h

        if video_ratio > target_ratio:
            # 영상이 더 넓음 - 높이 기준으로 맞추고 좌우 크롭
            new_h = target_h
            new_w = int(new_h * video_ratio)
            video = video.resized(height=new_h)

            # 중앙 크롭 (정수 좌표 사용)
            x_center = new_w // 2
            x1 = x_center - target_w // 2
            x2 = x1 + target_w
            video = video.cropped(x1=x1, x2=x2, y1=0, y2=target_h)
        else:
            # 영상이 더 좁거나 같음 - 너비 기준으로 맞추고 상하 크롭
            new_w = target_w
            new_h = int(new_w / video_ratio)
            video = video.resized(width=new_w)

            # 중앙 크롭 (정수 좌표 사용)
            y_center = new_h // 2
            y1 = y_center - target_h // 2
            y2 = y1 + target_h
            video = video.cropped(x1=0, x2=target_w, y1=y1, y2=y2)

        return video

    def _apply_cinematic_effects(self, video) -> VideoFileClip:
        """
        시네마틱 효과 적용 - AI Slop 회피 핵심
        1. 색 보정 (Stoic Navy + Gold)
        2. 비네팅 (화면 가장자리 어둡게)
        3. 필름 그레인 (디지털 매끄러움 제거)
        """
        # 1. 색 보정
        if self.config.color_grade_preset and self.config.color_grade_preset != 'none':
            try:
                video = apply_color_grade(video, self.config.color_grade_preset)
                logger.debug(f"색 보정 적용: {self.config.color_grade_preset}")
            except Exception as e:
                logger.warning(f"색 보정 실패: {e}")

        # 2. 비네팅
        if self.config.enable_vignette:
            try:
                video = add_vignette(video, self.config.vignette_intensity)
                logger.debug(f"비네팅 적용: intensity={self.config.vignette_intensity}")
            except Exception as e:
                logger.warning(f"비네팅 실패: {e}")

        # 3. 필름 그레인 (마지막에 적용)
        if self.config.enable_film_grain:
            try:
                video = add_film_grain(video, self.config.film_grain_intensity)
                logger.debug(f"필름 그레인 적용: intensity={self.config.film_grain_intensity}")
            except Exception as e:
                logger.warning(f"필름 그레인 실패: {e}")

        return video

    def _add_subtitles(
        self,
        video: VideoFileClip,
        srt_path: Path
    ) -> VideoFileClip:
        """자막 오버레이"""
        # SRT 파싱
        generator = SubtitleGenerator()
        entries = generator.parse_srt(srt_path)

        if not entries:
            return video

        # 자막 클립 생성
        subtitle_clips = []

        for entry in entries:
            try:
                txt_clip = self._create_text_clip(
                    entry.text,
                    entry.start_time,
                    entry.end_time - entry.start_time
                )
                subtitle_clips.append(txt_clip)
            except Exception as e:
                logger.warning(f"자막 클립 생성 실패: {e}")
                continue

        # 합성 (명시적 크기 지정 - 자막 짤림 방지)
        return CompositeVideoClip(
            [video] + subtitle_clips,
            size=(self.config.width, self.config.height)
        )

    def _create_text_clip(
        self,
        text: str,
        start: float,
        duration: float,
        is_highlight: bool = False
    ) -> TextClip:
        """텍스트 클립 생성"""
        fontsize = self.config.highlight_fontsize if is_highlight else self.config.subtitle_fontsize
        color = self.config.highlight_color if is_highlight else self.config.subtitle_color

        # 텍스트 전처리: 기존 줄바꿈 제거 후 균형 잡힌 줄바꿈 적용
        clean_text = ' '.join(text.split())
        wrapped_text = textwrap.fill(clean_text, width=self.config.subtitle_wrap_width)

        # MoviePy 2.x: method='label'로 직접 줄바꿈 처리
        # margin으로 상하 여유 추가 (stroke 짤림 방지)
        text_margin = self.config.subtitle_text_margin
        txt_clip = TextClip(
            text=wrapped_text,
            font=self.config.subtitle_font,
            font_size=fontsize,
            color=color,
            stroke_color=self.config.subtitle_stroke_color,
            stroke_width=self.config.subtitle_stroke_width,
            method='label',
            text_align='center',
            margin=(0, text_margin)
        )

        # 텍스트 높이 측정 (margin 포함)
        txt_height = txt_clip.h if hasattr(txt_clip, 'h') and txt_clip.h else 150

        # 하단 고정점 방식: 자막 하단이 항상 설정된 위치에 오도록
        # (화면 높이 - 하단 여백 = 자막 하단 위치)
        desired_bottom = self.config.height - self.config.subtitle_bottom_margin
        y_pos = desired_bottom - txt_height

        # 최소 위치 보장 (화면 중앙 아래로)
        min_y = int(self.config.height * 0.45)
        y_pos = max(y_pos, min_y)

        # 위치 설정
        x_pos = self.config.subtitle_position[0]
        txt_clip = txt_clip.with_position((x_pos, y_pos))
        txt_clip = txt_clip.with_start(start)
        txt_clip = txt_clip.with_duration(duration)

        return txt_clip

    def _mix_audio(
        self,
        voice: AudioFileClip,
        bgm_path: Path,
        duration: float
    ) -> CompositeAudioClip:
        """음성과 BGM 믹싱"""
        bgm = AudioFileClip(str(bgm_path))

        # BGM 루프 (필요시)
        if bgm.duration < duration:
            # 필요한 만큼 반복
            loops = int(duration / bgm.duration) + 1
            bgm = concatenate_audioclips([bgm] * loops)

        # 길이 맞추기
        bgm = bgm.subclipped(0, duration)

        # 볼륨 조절 및 페이드 인/아웃 (MoviePy 2.x)
        bgm = bgm.with_effects([
            MultiplyVolume(self.config.bgm_volume),
            AudioFadeIn(self.config.bgm_fade_in),
            AudioFadeOut(self.config.bgm_fade_out)
        ])

        return CompositeAudioClip([voice, bgm])


def concatenate_audioclips(clips):
    """오디오 클립 연결 (헬퍼 함수)"""
    from moviepy import concatenate_audioclips as _concat
    return _concat(clips)


class QuickComposer:
    """빠른 영상 합성 (간단한 인터페이스)"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir or "./output")
        self.composer = VideoComposer()

    def create_simple_video(
        self,
        audio_path: Path,
        text: str,
        background_color: Tuple[int, int, int] = (0, 0, 0),
        output_name: str = None
    ) -> Path:
        """간단한 텍스트 영상 생성"""
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        # 배경
        video = ColorClip(
            size=(1080, 1920),
            color=background_color,
            duration=duration
        )

        # 텍스트 (MoviePy 2.x)
        txt_clip = TextClip(
            text=text,
            font="NotoSansKR-Bold",
            font_size=60,
            color="white",
            method='caption',
            size=(980, None),
            text_align='center'
        ).with_position('center').with_duration(duration)

        # 합성
        final = CompositeVideoClip([video, txt_clip])
        final = final.with_audio(audio)

        # 저장
        output_name = output_name or "simple_video.mp4"
        output_path = self.output_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            threads=OPTIMAL_THREADS,
            logger=None
        )

        final.close()
        audio.close()

        return output_path
