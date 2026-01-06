"""
FFmpeg 직접 호출 영상 합성 모듈
MoviePy 대신 FFmpeg subprocess를 사용하여 20분 → 1분 이하로 단축

4단계 파이프라인:
1. concat + scale/crop (B-roll 연결)
2. audio merge (오디오 합성)
3. subtitles (ASS 자막 오버레이)
4. effects (색보정/비네팅/그레인)
"""

import subprocess
import shutil
import time
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent


# =============================================================================
# FFmpeg 경로 및 인코더 감지
# =============================================================================

def get_ffmpeg_path() -> str:
    """FFmpeg 실행 파일 경로 반환"""
    # 1. 시스템 PATH에서 찾기
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    # 2. MoviePy/imageio에서 찾기
    try:
        from moviepy.config import FFMPEG_BINARY
        if Path(FFMPEG_BINARY).exists():
            return FFMPEG_BINARY
    except:
        pass

    # 3. imageio_ffmpeg에서 직접 찾기
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        pass

    raise RuntimeError("FFmpeg를 찾을 수 없습니다. 설치해주세요.")


def detect_encoder() -> str:
    """사용 가능한 최적 인코더 감지"""
    ffmpeg = get_ffmpeg_path()
    result = subprocess.run(
        [ffmpeg, '-encoders'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    output = result.stdout + result.stderr

    # 우선순위: NVIDIA > Intel > AMD > CPU
    if 'h264_nvenc' in output:
        logger.info("NVENC (NVIDIA GPU) 인코더 사용")
        return 'h264_nvenc'
    elif 'h264_qsv' in output:
        logger.info("QuickSync (Intel GPU) 인코더 사용")
        return 'h264_qsv'
    elif 'h264_amf' in output:
        logger.info("AMF (AMD GPU) 인코더 사용")
        return 'h264_amf'
    else:
        logger.info("libx264 (CPU) 인코더 사용")
        return 'libx264'


# =============================================================================
# 설정
# =============================================================================

@dataclass
class FFmpegConfig:
    """FFmpeg 합성 설정"""
    # 영상 크기
    width: int = 1080
    height: int = 1920
    fps: int = 30

    # 인코딩 (자동 감지)
    encoder: str = ""  # 빈 문자열이면 자동 감지

    # NVENC 설정 (CQ 모드 - 파일 크기 최적화)
    nvenc_preset: str = "p4"  # p1(fastest)~p7(slowest), p4=balanced
    nvenc_cq: int = 26  # 26으로 올려서 12-16MB 목표
    nvenc_maxrate: str = "6M"
    nvenc_bufsize: str = "12M"

    # CPU 폴백 설정
    cpu_preset: str = "fast"
    cpu_crf: int = 24

    # 오디오
    audio_codec: str = "aac"
    audio_bitrate: str = "128k"

    # 시네마틱 효과 (현재 video_composer.py와 동일)
    enable_color_grade: bool = True
    color_red_shift: float = 0.1   # 붉은 톤
    color_blue_shift: float = 0.05  # 푸른 톤
    saturation: float = 0.85
    contrast: float = 1.12

    enable_vignette: bool = True
    vignette_angle: str = "PI/5"  # 비네팅 강도

    enable_grain: bool = True
    grain_strength: int = 6  # 6으로 낮춰서 속도/크기 개선

    # 자막 (Stoic 스타일)
    subtitle_font: str = "Malgun Gothic Bold"
    subtitle_fontsize: int = 60
    subtitle_color: str = "&H00D7FF"  # FFmpeg ASS 형식 (BGR, 금색)
    subtitle_outline_color: str = "&H000000"
    subtitle_outline_width: int = 3
    subtitle_margin_bottom: int = 280


def load_preset(preset_name: str = "v1") -> FFmpegConfig:
    """preset 파일에서 설정 로드"""
    preset_path = PROJECT_ROOT / "config" / f"preset_{preset_name}.json"
    if not preset_path.exists():
        logger.warning(f"Preset {preset_name} not found, using defaults")
        return FFmpegConfig()

    with open(preset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    config = FFmpegConfig()

    # video
    if 'video' in data:
        config.width = data['video'].get('width', config.width)
        config.height = data['video'].get('height', config.height)
        config.fps = data['video'].get('fps', config.fps)

    # encoding
    if 'encoding' in data:
        enc = data['encoding']
        if 'nvenc' in enc:
            config.nvenc_preset = enc['nvenc'].get('preset', config.nvenc_preset)
            config.nvenc_cq = enc['nvenc'].get('cq', config.nvenc_cq)
            config.nvenc_maxrate = enc['nvenc'].get('maxrate', config.nvenc_maxrate)
            config.nvenc_bufsize = enc['nvenc'].get('bufsize', config.nvenc_bufsize)
        if 'cpu_fallback' in enc:
            config.cpu_preset = enc['cpu_fallback'].get('preset', config.cpu_preset)
            config.cpu_crf = enc['cpu_fallback'].get('crf', config.cpu_crf)
        if 'audio' in enc:
            config.audio_codec = enc['audio'].get('codec', config.audio_codec)
            config.audio_bitrate = enc['audio'].get('bitrate', config.audio_bitrate)

    # effects
    if 'effects' in data:
        fx = data['effects']
        if 'color_grade' in fx:
            config.enable_color_grade = fx['color_grade'].get('enabled', config.enable_color_grade)
            config.color_red_shift = fx['color_grade'].get('red_shift', config.color_red_shift)
            config.color_blue_shift = fx['color_grade'].get('blue_shift', config.color_blue_shift)
            config.saturation = fx['color_grade'].get('saturation', config.saturation)
            config.contrast = fx['color_grade'].get('contrast', config.contrast)
        if 'vignette' in fx:
            config.enable_vignette = fx['vignette'].get('enabled', config.enable_vignette)
            config.vignette_angle = fx['vignette'].get('angle', config.vignette_angle)
        if 'grain' in fx:
            config.enable_grain = fx['grain'].get('enabled', config.enable_grain)
            config.grain_strength = fx['grain'].get('strength', config.grain_strength)

    # subtitle
    if 'subtitle' in data:
        sub = data['subtitle']
        config.subtitle_font = sub.get('font', config.subtitle_font)
        config.subtitle_fontsize = sub.get('fontsize', config.subtitle_fontsize)
        config.subtitle_color = sub.get('color', config.subtitle_color)
        config.subtitle_outline_color = sub.get('outline_color', config.subtitle_outline_color)
        config.subtitle_outline_width = sub.get('outline_width', config.subtitle_outline_width)
        config.subtitle_margin_bottom = sub.get('margin_bottom', config.subtitle_margin_bottom)

    return config


# =============================================================================
# SRT → ASS 변환
# =============================================================================

def srt_to_ass(srt_path: Path, ass_path: Path, config: FFmpegConfig) -> Path:
    """SRT 자막을 ASS 형식으로 변환"""

    # ASS 헤더
    ass_header = f"""[Script Info]
Title: Shorts Subtitle
ScriptType: v4.00+
PlayResX: {config.width}
PlayResY: {config.height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{config.subtitle_font},{config.subtitle_fontsize},{config.subtitle_color},&H000000FF,{config.subtitle_outline_color},&H00000000,1,0,0,0,100,100,0,0,1,{config.subtitle_outline_width},0,2,20,20,{config.subtitle_margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # SRT 파싱
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    blocks = re.split(r'\n\n+', content.strip())

    dialogues = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # 시간 파싱
            time_match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})',
                lines[1]
            )
            if time_match:
                # SRT: 00:00:00,000 → ASS: 0:00:00.00
                start = f"{int(time_match.group(1))}:{time_match.group(2)}:{time_match.group(3)}.{time_match.group(4)[:2]}"
                end = f"{int(time_match.group(5))}:{time_match.group(6)}:{time_match.group(7)}.{time_match.group(8)[:2]}"

                # 텍스트 (줄바꿈은 \N으로)
                text = '\\N'.join(lines[2:])

                dialogues.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    # ASS 파일 작성
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        f.write('\n'.join(dialogues))

    return ass_path


# =============================================================================
# FFmpeg 합성기
# =============================================================================

class FFmpegComposer:
    """FFmpeg 직접 호출 영상 합성기"""

    def __init__(self, config: FFmpegConfig = None):
        self.config = config or FFmpegConfig()
        self.ffmpeg = get_ffmpeg_path()

        # 인코더 자동 감지
        if not self.config.encoder:
            self.config.encoder = detect_encoder()

    def compose(
        self,
        audio_path: Path,
        broll_clips: List,  # BrollClip 리스트
        srt_path: Optional[Path] = None,
        bgm_path: Optional[Path] = None,
        output_path: Path = None,
        enable_effects: bool = True
    ) -> Tuple[Path, float]:
        """
        영상 합성 (4단계 파이프라인)

        Returns:
            (output_path, elapsed_seconds)
        """
        start_time = time.time()

        audio_path = Path(audio_path)
        output_path = Path(output_path) if output_path else audio_path.with_suffix('.mp4')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = output_path.parent / "temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            # 오디오 길이 확인
            duration = self._get_duration(audio_path)
            logger.info(f"오디오 길이: {duration:.1f}초")

            # 1단계: B-roll concat + scale/crop
            logger.info("[1/4] B-roll 연결 및 리사이즈...")
            concat_path = temp_dir / "step1_concat.mp4"
            self._step1_concat_broll(broll_clips, duration, concat_path)

            # 2단계: 오디오 합성
            logger.info("[2/4] 오디오 합성...")
            audio_merged_path = temp_dir / "step2_audio.mp4"
            self._step2_merge_audio(concat_path, audio_path, bgm_path, audio_merged_path)

            # 3단계: 자막 오버레이
            if srt_path and Path(srt_path).exists():
                logger.info("[3/4] 자막 오버레이...")
                subtitle_path = temp_dir / "step3_subtitle.mp4"
                ass_path = temp_dir / "captions.ass"
                srt_to_ass(srt_path, ass_path, self.config)
                self._step3_add_subtitles(audio_merged_path, ass_path, subtitle_path)
                current_path = subtitle_path
            else:
                logger.info("[3/4] 자막 없음, 스킵")
                current_path = audio_merged_path

            # 4단계: 효과 적용 + 최종 인코딩
            if enable_effects:
                logger.info("[4/4] 효과 적용 및 최종 인코딩...")
                self._step4_apply_effects(current_path, output_path)
            else:
                logger.info("[4/4] 효과 없이 최종 인코딩...")
                self._step4_finalize(current_path, output_path)

            elapsed = time.time() - start_time
            logger.info(f"[완료] {elapsed:.1f}초 소요")

            return output_path, elapsed

        finally:
            # 임시 파일 정리
            self._cleanup_temp(temp_dir)

    def _get_duration(self, audio_path: Path) -> float:
        """오디오 길이 확인"""
        result = subprocess.run([
            self.ffmpeg, '-i', str(audio_path),
            '-f', 'null', '-'
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        import re
        match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', result.stderr)
        if match:
            h, m, s, ms = map(int, match.groups())
            return h * 3600 + m * 60 + s + ms / 100
        return 30.0  # 기본값

    def _step1_concat_broll(
        self,
        broll_clips: List,
        target_duration: float,
        output_path: Path
    ):
        """1단계: B-roll 연결 + 리사이즈"""
        temp_dir = output_path.parent

        # 클립 파일 목록 생성
        clips_txt = temp_dir / "clips.txt"
        valid_clips = []
        total_duration = 0.0

        for broll in broll_clips:
            if not broll.path.exists():
                continue

            # 클립 길이 확인
            clip_duration = self._get_duration(broll.path)
            use_duration = min(clip_duration, 6.0, target_duration - total_duration)

            if use_duration <= 0:
                break

            valid_clips.append((broll.path, use_duration))
            total_duration += use_duration

        # 길이가 부족하면 마지막 클립 반복
        while total_duration < target_duration and valid_clips:
            last_path, last_dur = valid_clips[-1]
            remaining = target_duration - total_duration
            use_duration = min(last_dur, remaining)
            valid_clips.append((last_path, use_duration))
            total_duration += use_duration

        # 각 클립을 리사이즈해서 임시 파일로 저장
        resized_clips = []
        for i, (clip_path, clip_dur) in enumerate(valid_clips):
            resized_path = temp_dir / f"clip_{i:03d}.mp4"

            # 리사이즈 + 크롭 + 길이 제한
            cmd = [
                self.ffmpeg, '-y',
                '-i', str(clip_path),
                '-t', str(clip_dur),
                '-vf', f'scale={self.config.width}:{self.config.height}:force_original_aspect_ratio=increase,crop={self.config.width}:{self.config.height},fps={self.config.fps}',
                '-an',  # 오디오 제거
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
                str(resized_path)
            ]

            subprocess.run(cmd, capture_output=True)

            if resized_path.exists():
                resized_clips.append(resized_path)

        # concat 파일 생성
        with open(clips_txt, 'w', encoding='utf-8') as f:
            for clip_path in resized_clips:
                # Windows 경로 처리
                safe_path = str(clip_path).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        # concat 실행
        cmd = [
            self.ffmpeg, '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(clips_txt),
            '-c', 'copy',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            logger.error(f"concat 실패: {result.stderr}")
            raise RuntimeError("B-roll concat 실패")

        # 리사이즈된 임시 클립 삭제
        for clip_path in resized_clips:
            try:
                clip_path.unlink()
            except:
                pass

    def _step2_merge_audio(
        self,
        video_path: Path,
        audio_path: Path,
        bgm_path: Optional[Path],
        output_path: Path
    ):
        """2단계: 오디오 합성"""
        if bgm_path and Path(bgm_path).exists():
            # BGM + 음성 믹싱
            cmd = [
                self.ffmpeg, '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-i', str(bgm_path),
                '-filter_complex', '[1:a]volume=1.0[voice];[2:a]volume=0.2,afade=t=in:d=1,afade=t=out:d=2:st=-2[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]',
                '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy',
                '-c:a', self.config.audio_codec, '-b:a', self.config.audio_bitrate,
                '-shortest',
                str(output_path)
            ]
        else:
            # 음성만
            cmd = [
                self.ffmpeg, '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy',
                '-c:a', self.config.audio_codec, '-b:a', self.config.audio_bitrate,
                '-shortest',
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            logger.error(f"오디오 합성 실패: {result.stderr}")
            raise RuntimeError("오디오 합성 실패")

    def _step3_add_subtitles(
        self,
        video_path: Path,
        ass_path: Path,
        output_path: Path
    ):
        """3단계: 자막 오버레이"""
        # Windows 경로에서 백슬래시를 이스케이프
        ass_path_escaped = str(ass_path).replace('\\', '/').replace(':', '\\:')

        cmd = [
            self.ffmpeg, '-y',
            '-i', str(video_path),
            '-vf', f"subtitles='{ass_path_escaped}'",
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
            '-c:a', 'copy',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            logger.error(f"자막 오버레이 실패: {result.stderr}")
            # 자막 실패 시 원본 복사
            shutil.copy(video_path, output_path)

    def _step4_apply_effects(self, input_path: Path, output_path: Path):
        """4단계: 효과 적용 + 최종 인코딩 (GPU)"""
        filters = []

        # 색 보정
        if self.config.enable_color_grade:
            filters.append(f"colorbalance=rs={self.config.color_red_shift}:bs={self.config.color_blue_shift}")
            filters.append(f"eq=saturation={self.config.saturation}:contrast={self.config.contrast}")

        # 비네팅
        if self.config.enable_vignette:
            filters.append(f"vignette=angle={self.config.vignette_angle}")

        # 그레인 (성능에 영향 큼 - 필요시 강도 줄이기)
        if self.config.enable_grain:
            filters.append(f"noise=alls={self.config.grain_strength}:allf=t")

        filter_chain = ','.join(filters) if filters else 'null'

        # 인코딩 설정
        if self.config.encoder == 'h264_nvenc':
            encode_opts = [
                '-c:v', 'h264_nvenc',
                '-preset', self.config.nvenc_preset,
                '-rc', 'vbr',
                '-cq', str(self.config.nvenc_cq),
                '-maxrate', self.config.nvenc_maxrate,
                '-bufsize', '16M',
                '-profile:v', 'high',
            ]
        else:
            encode_opts = [
                '-c:v', 'libx264',
                '-preset', self.config.cpu_preset,
                '-crf', str(self.config.cpu_crf),
            ]

        cmd = [
            self.ffmpeg, '-y',
            '-i', str(input_path),
            '-vf', filter_chain,
            *encode_opts,
            '-c:a', 'copy',
            '-movflags', '+faststart',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            logger.error(f"효과 적용 실패: {result.stderr}")
            raise RuntimeError("효과 적용 실패")

    def _step4_finalize(self, input_path: Path, output_path: Path):
        """4단계: 효과 없이 최종 인코딩"""
        # 인코딩 설정
        if self.config.encoder == 'h264_nvenc':
            encode_opts = [
                '-c:v', 'h264_nvenc',
                '-preset', self.config.nvenc_preset,
                '-rc', 'vbr',
                '-cq', str(self.config.nvenc_cq),
            ]
        else:
            encode_opts = [
                '-c:v', 'libx264',
                '-preset', self.config.cpu_preset,
                '-crf', str(self.config.cpu_crf),
            ]

        cmd = [
            self.ffmpeg, '-y',
            '-i', str(input_path),
            *encode_opts,
            '-c:a', 'copy',
            '-movflags', '+faststart',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            logger.error(f"최종 인코딩 실패: {result.stderr}")
            raise RuntimeError("최종 인코딩 실패")

    def _cleanup_temp(self, temp_dir: Path):
        """임시 파일 정리"""
        try:
            for f in temp_dir.glob("*"):
                try:
                    f.unlink()
                except:
                    pass
            temp_dir.rmdir()
        except:
            pass


# =============================================================================
# 테스트 함수
# =============================================================================

def test_ffmpeg_composer():
    """FFmpeg Composer 테스트"""
    print("=" * 50)
    print("FFmpeg Composer 테스트")
    print("=" * 50)

    # 1. FFmpeg 경로 확인
    ffmpeg = get_ffmpeg_path()
    print(f"[OK] FFmpeg 경로: {ffmpeg}")

    # 2. 인코더 감지
    encoder = detect_encoder()
    print(f"[OK] 감지된 인코더: {encoder}")

    # 3. 설정 출력
    config = FFmpegConfig()
    config.encoder = encoder
    print(f"[OK] 설정:")
    print(f"     - 해상도: {config.width}x{config.height}")
    print(f"     - FPS: {config.fps}")
    print(f"     - 인코더: {config.encoder}")

    print("=" * 50)
    print("테스트 완료!")
    print("=" * 50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_ffmpeg_composer()
