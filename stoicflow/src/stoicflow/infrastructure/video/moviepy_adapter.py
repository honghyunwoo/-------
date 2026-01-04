"""MoviePy 2.x video editor adapter."""

from pathlib import Path
from typing import Any
import uuid

from loguru import logger

from stoicflow.application.interfaces.video_editor import VideoEditor
from stoicflow.config.settings import settings
from stoicflow.domain.entities.video import Video, VideoSpec, VideoStatus
from stoicflow.domain.value_objects.audio import AudioClip
from stoicflow.domain.value_objects.subtitle import Subtitle


class MoviePyAdapter(VideoEditor):
    """
    MoviePy 2.x를 사용하는 비디오 편집 어댑터.

    MoviePy 2.x API 호환:
    - volumex() → with_effects([afx.MultiplyVolume()])
    - set_audio() → with_audio()
    - set_position() → with_position()
    """

    async def compose(
        self,
        output_path: Path,
        spec: VideoSpec,
        background: Path | None = None,
        audio: AudioClip | None = None,
        subtitles: list[Subtitle] | None = None,
        background_music: Path | None = None,
        background_music_volume: float = 0.1,
    ) -> Video:
        """비디오 컴포지션 생성."""
        from moviepy import (
            AudioFileClip,
            ColorClip,
            CompositeVideoClip,
            ImageClip,
            TextClip,
            VideoFileClip,
            concatenate_audioclips,
        )
        from moviepy.audio import fx as afx

        logger.info(f"Composing video: {spec.resolution}")

        # Determine duration from audio
        duration = audio.duration if audio else 30.0

        # Create background
        if background and background.exists():
            if background.suffix.lower() in [".mp4", ".mov", ".avi", ".webm"]:
                bg_clip = VideoFileClip(str(background))
                # Loop or trim to match audio duration
                if bg_clip.duration < duration:
                    bg_clip = bg_clip.loop(duration=duration)
                else:
                    bg_clip = bg_clip.subclipped(0, duration)
                # Resize to spec
                bg_clip = bg_clip.resized((spec.width, spec.height))
            else:
                # Image background
                bg_clip = (
                    ImageClip(str(background))
                    .with_duration(duration)
                    .resized((spec.width, spec.height))
                )
        else:
            # Solid color background (dark)
            bg_clip = ColorClip(
                size=(spec.width, spec.height),
                color=(20, 20, 30),
                duration=duration,
            )

        clips = [bg_clip]

        # Add subtitles
        if subtitles:
            for sub in subtitles:
                txt_clip = self._create_subtitle_clip(sub, spec)
                clips.append(txt_clip)

        # Composite video
        video = CompositeVideoClip(clips, size=(spec.width, spec.height))
        video = video.with_duration(duration)

        # Handle audio
        audio_clips = []

        if audio:
            main_audio = AudioFileClip(str(audio.path))
            audio_clips.append(main_audio)

        if background_music and background_music.exists():
            music = AudioFileClip(str(background_music))
            # Loop music if needed
            if music.duration < duration:
                music = music.loop(duration=duration)
            else:
                music = music.subclipped(0, duration)
            # Reduce volume
            music = music.with_effects([afx.MultiplyVolume(background_music_volume)])
            audio_clips.append(music)

        if audio_clips:
            if len(audio_clips) == 1:
                final_audio = audio_clips[0]
            else:
                # Mix audio tracks
                from moviepy import CompositeAudioClip

                final_audio = CompositeAudioClip(audio_clips)
            video = video.with_audio(final_audio)

        # Export
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Rendering video to {output_path}")

        video.write_videofile(
            str(output_path),
            fps=spec.fps,
            codec=spec.codec,
            audio_codec=spec.audio_codec,
            bitrate=spec.bitrate,
            logger=None,  # Suppress moviepy output
        )

        # Cleanup
        video.close()
        bg_clip.close()

        return Video(
            id=str(uuid.uuid4())[:8],
            script_id=0,  # Will be set by caller
            title="",  # Will be set by caller
            video_path=output_path,
            audio_path=audio.path if audio else None,
            spec=spec,
            duration=duration,
            status=VideoStatus.COMPOSED,
        )

    def _create_subtitle_clip(self, subtitle: Subtitle, spec: VideoSpec) -> Any:
        """자막 클립 생성."""
        from moviepy import TextClip

        style = subtitle.style

        # Find font
        font = self._find_font(style.font_family)

        txt_clip = TextClip(
            text=subtitle.text,
            font=font,
            font_size=style.font_size,
            color=style.color,
            stroke_color=style.stroke_color,
            stroke_width=style.stroke_width,
            method="caption",
            size=(style.max_width, None),
            text_align="center",
        )

        # Position at bottom center
        txt_clip = txt_clip.with_position(("center", spec.height - style.margin_bottom - 100))

        # Set timing
        txt_clip = txt_clip.with_start(subtitle.start_time).with_duration(subtitle.duration)

        return txt_clip

    def _find_font(self, font_family: str) -> str:
        """시스템에서 폰트 경로 찾기."""
        import platform

        system = platform.system()

        # Common font paths by OS
        font_paths = {
            "Darwin": [  # macOS
                f"/System/Library/Fonts/{font_family}.ttf",
                f"/Library/Fonts/{font_family}.ttf",
                f"~/Library/Fonts/{font_family}.ttf",
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            ],
            "Linux": [
                f"/usr/share/fonts/truetype/{font_family}.ttf",
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ],
            "Windows": [
                f"C:\\Windows\\Fonts\\{font_family}.ttf",
                "C:\\Windows\\Fonts\\malgun.ttf",
            ],
        }

        for path in font_paths.get(system, []):
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)

        # Fallback to default
        logger.warning(f"Font {font_family} not found, using default")
        return "DejaVu-Sans"

    async def add_subtitles(
        self,
        video_path: Path,
        subtitles: list[Subtitle],
        output_path: Path,
    ) -> Path:
        """기존 비디오에 자막 추가."""
        from moviepy import CompositeVideoClip, VideoFileClip

        video = VideoFileClip(str(video_path))
        spec = VideoSpec(width=video.w, height=video.h)

        clips = [video]
        for sub in subtitles:
            clips.append(self._create_subtitle_clip(sub, spec))

        final = CompositeVideoClip(clips)
        final.write_videofile(str(output_path), logger=None)

        video.close()
        final.close()

        return output_path

    async def get_duration(self, media_path: Path) -> float:
        """미디어 파일의 길이 반환."""
        suffix = media_path.suffix.lower()

        if suffix in [".mp4", ".mov", ".avi", ".webm", ".mkv"]:
            from moviepy import VideoFileClip

            with VideoFileClip(str(media_path)) as clip:
                return clip.duration
        elif suffix in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
            from moviepy import AudioFileClip

            with AudioFileClip(str(media_path)) as clip:
                return clip.duration
        else:
            raise ValueError(f"Unsupported media format: {suffix}")

    async def extract_audio(self, video_path: Path, output_path: Path) -> AudioClip:
        """비디오에서 오디오 추출."""
        from moviepy import VideoFileClip

        video = VideoFileClip(str(video_path))
        audio = video.audio

        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio.write_audiofile(str(output_path), logger=None)

        duration = audio.duration
        video.close()

        return AudioClip(
            path=output_path,
            duration=duration,
        )

    async def create_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float = 0.0,
    ) -> Path:
        """비디오에서 썸네일 생성."""
        from moviepy import VideoFileClip

        video = VideoFileClip(str(video_path))

        # Get frame at timestamp
        frame = video.get_frame(timestamp)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        from PIL import Image

        img = Image.fromarray(frame)
        img.save(str(output_path))

        video.close()

        return output_path
