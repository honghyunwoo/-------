# -*- coding: utf-8 -*-
"""
최고 품질 영상 생성 스크립트
- 스토아 철학 B-roll (조각상, 폭풍, 일출)
- 수정된 자막 시스템
- BGM 포함
"""

from pathlib import Path
from core.video_composer import VideoComposer, CompositionConfig
from core.broll_selector import BrollSelector, BrollConfig

# 경로 설정
output_dir = Path("output/2026-01-04_quote_3")
audio_path = output_dir / "audio.mp3"
srt_path = output_dir / "captions.srt"
output_path = output_dir / "video_best.mp4"

# BGM 확인
bgm_dir = Path("assets/bgm")
bgm_files = list(bgm_dir.glob("*.mp3")) if bgm_dir.exists() else []

print("="*60)
print("최고 품질 영상 생성")
print("="*60)
print(f"오디오: {audio_path}")
print(f"자막: {srt_path}")
print(f"출력: {output_path}")
print(f"BGM 파일: {len(bgm_files)}개")

# 오디오 길이 확인
from moviepy import AudioFileClip
audio = AudioFileClip(str(audio_path))
duration = audio.duration
audio.close()
print(f"오디오 길이: {duration:.1f}초")

# B-roll 선택 (스토아 철학 테마)
print("\n[1/3] B-roll 선택...")
broll_config = BrollConfig(assets_path=Path("assets/b-roll"))
broll_selector = BrollSelector(broll_config)

# 스토아 철학에 어울리는 키워드
stoic_themes = [
    "stoic", "statue", "meditation",
    "storm", "adversity", "sunrise",
    "dark", "cinematic", "epic"
]
broll_clips = broll_selector.select(stoic_themes, duration)
print(f"  선택된 클립: {len(broll_clips)}개")

for i, clip in enumerate(broll_clips[:5]):
    print(f"    {i+1}. {clip.path.name} ({clip.duration:.1f}s)")

# 영상 합성 설정
print("\n[2/3] 영상 합성 설정...")
config = CompositionConfig(
    width=1080,
    height=1920,
    fps=30,
    codec="libx264",
    bitrate="8M",  # 고품질

    # 자막 설정
    subtitle_font="C:/Windows/Fonts/malgun.ttf",
    subtitle_fontsize=48,
    subtitle_color="white",
    subtitle_stroke_color="black",
    subtitle_stroke_width=2,

    # BGM 설정
    bgm_volume=0.15,  # 낮은 볼륨
    bgm_fade_in=1.0,
    bgm_fade_out=2.0
)

composer = VideoComposer(config)

# BGM 선택
bgm_path = bgm_files[0] if bgm_files else None
if bgm_path:
    print(f"  BGM: {bgm_path.name}")
else:
    print("  BGM: 없음")

# 영상 합성
print("\n[3/3] 영상 합성 중...")
video_path = composer.compose(
    audio_path=audio_path,
    broll_clips=broll_clips,
    srt_path=srt_path,
    bgm_path=bgm_path,
    output_path=output_path
)

print("\n" + "="*60)
print(f"[완료] {video_path}")
print("="*60)

# 파일 크기 확인
import os
size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"파일 크기: {size_mb:.1f} MB")
