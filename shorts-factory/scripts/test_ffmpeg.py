"""
FFmpeg Composer 실제 영상 테스트
기존 MoviePy 결과와 A/B 비교용
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tts_engine import TTSEngine, TTSProvider
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector
from core.ffmpeg_composer import FFmpegComposer, FFmpegConfig


def test_ffmpeg_single(script_id: int = 1):
    """FFmpeg로 단일 영상 생성 테스트"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "output"
    assets_dir = project_root / "assets" / "b-roll"

    # 스크립트 로드
    scripts_file = data_dir / "scripts_pilot_20.json"
    with open(scripts_file, 'r', encoding='utf-8') as f:
        scripts = json.load(f)

    script = next((s for s in scripts if s["id"] == script_id), None)
    if not script:
        print(f"[ERROR] Script ID {script_id} not found")
        return

    # 프로젝트 디렉토리 (FFmpeg 버전)
    date_str = datetime.now().strftime("%Y%m%d")
    project_id = f"{date_str}_{script['category']}_{script_id:02d}_ffmpeg"
    project_dir = output_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[FFmpeg Test] Script ID {script_id}")
    print(f"{'='*60}")
    print(f"[Project] {project_id}")
    print(f"[Category] {script['category']}")
    print(f"[Topic] {script['topic']}")
    print(f"{'='*60}\n")

    total_start = time.time()

    # 1. TTS 생성
    print("[1/4] TTS 생성...")
    tts_text = " ".join([
        script.get("s1_hook", ""),
        script.get("s2_pain", ""),
        script.get("s3_insight", ""),
        script.get("s4_action", ""),
        script.get("s5_result", ""),
        script.get("s6_loop_cta", "")
    ])
    tts_path = project_dir / "audio.mp3"

    tts_start = time.time()
    tts = TTSEngine(provider=TTSProvider.EDGE, lang="ko")
    tts.generate(tts_text, tts_path)
    tts_time = time.time() - tts_start
    print(f"     [OK] TTS 완료 ({tts_time:.1f}초)")

    # 오디오 길이 확인
    from moviepy import AudioFileClip
    with AudioFileClip(str(tts_path)) as audio:
        duration = audio.duration
    print(f"     Audio duration: {duration:.1f}초")

    # 2. 자막 생성
    print("[2/4] 자막 생성...")
    srt_path = project_dir / "captions.srt"
    subtitle_gen = SubtitleGenerator()
    subtitle_gen.generate_from_script(tts_text, duration, srt_path)
    print(f"     [OK] SRT 생성 완료")

    # 3. B-roll 선택
    print("[3/4] B-roll 선택...")
    selector = BrollSelector(assets_path=assets_dir)

    mood_themes = {
        "calm": ["meditation", "nature"],
        "dramatic": ["dark_cinematic", "storm_adversity"],
        "hopeful": ["sunrise_hope", "nature_epic"],
        "reflective": ["sunset_reflection", "time_passing"]
    }
    themes = mood_themes.get(script.get("mood", "dramatic"), ["nature_epic"])
    themes.extend(script.get("broll_keywords", []))

    clips = selector.select(themes, duration)
    print(f"     [OK] B-roll {len(clips)}개 선택")

    # 4. FFmpeg 합성
    print("[4/4] FFmpeg 합성...")
    video_path = project_dir / "video.mp4"

    compose_start = time.time()
    composer = FFmpegComposer()
    result_path, compose_time = composer.compose(
        audio_path=tts_path,
        broll_clips=clips,
        srt_path=srt_path,
        output_path=video_path
    )
    print(f"     [OK] 합성 완료 ({compose_time:.1f}초)")

    total_time = time.time() - total_start

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"[DONE] FFmpeg 테스트 완료!")
    print(f"{'='*60}")
    print(f"[VIDEO] {result_path}")
    print(f"[SIZE] {result_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\n[TIME BREAKDOWN]")
    print(f"  TTS:     {tts_time:.1f}초")
    print(f"  합성:    {compose_time:.1f}초")
    print(f"  ----------------------")
    print(f"  총 소요: {total_time:.1f}초")
    print(f"{'='*60}\n")

    # 성공 기준 체크
    if compose_time < 60:
        print("[PASS] 목표 달성: 합성 시간 < 60초")
    else:
        print(f"[WARN] 목표 미달: 합성 시간 {compose_time:.1f}초 > 60초")

    return result_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, default=1, help="Script ID")
    args = parser.parse_args()

    test_ffmpeg_single(args.id)
