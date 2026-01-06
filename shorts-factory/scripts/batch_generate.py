"""
Batch Generate - 파일럿 스크립트 배치 생성
새로운 6문장 형식 (s1~s6)을 지원합니다.

사용법:
    python scripts/batch_generate.py --id 1
    python scripts/batch_generate.py --all
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import logging
from core.tts_engine import TTSEngine, TTSProvider
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector
from core.ffmpeg_composer import FFmpegComposer, load_preset
from core.thumbnail_generator import ThumbnailGenerator
from core.upload_packager import UploadPackager


@dataclass
class ModularScript:
    """6문장 형식 스크립트 (V2 호환)"""
    id: int
    category: str
    topic: str
    mood: str
    s1_hook: str
    s2_pain: str
    s3_reframe: str  # V2: 관점 전환
    s4_insight: str  # V2: 통찰
    s5_action: str   # V2: 행동 제안
    s6_loop_cta: str
    broll_keywords: List[str]
    version: str = "v2"
    cta_type: str = "acknowledge"

    @classmethod
    def from_json(cls, data: dict) -> 'ModularScript':
        # V1/V2 호환: V1 필드명도 지원
        return cls(
            id=data.get("id", 0),
            category=data.get("category", ""),
            topic=data.get("topic", ""),
            mood=data.get("mood", "empathetic"),
            s1_hook=data.get("s1_hook", ""),
            s2_pain=data.get("s2_pain", ""),
            s3_reframe=data.get("s3_reframe", data.get("s3_insight", "")),
            s4_insight=data.get("s4_insight", data.get("s4_action", "")),
            s5_action=data.get("s5_action", data.get("s5_result", "")),
            s6_loop_cta=data.get("s6_loop_cta", ""),
            broll_keywords=data.get("broll_keywords", []),
            version=data.get("version", "v2"),
            cta_type=data.get("cta_type", "acknowledge")
        )

    def to_tts_text(self) -> str:
        """TTS용 텍스트 - 6문장 순서대로"""
        sentences = [
            self.s1_hook,
            self.s2_pain,
            self.s3_reframe,
            self.s4_insight,
            self.s5_action,
            self.s6_loop_cta
        ]
        return " ".join(s for s in sentences if s)

    def get_project_id(self) -> str:
        """프로젝트 ID 생성"""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{date_str}_{self.category}_{self.id:02d}"


def _worker_produce(script_dict: dict, output_dir: str, assets_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """
    병렬 처리용 워커 함수 (모듈 레벨에서 정의 - pickle 가능)

    Returns:
        (result_path, error): 성공 시 (path, None), 실패 시 (None, error_msg)
    """
    try:
        from core.tts_engine import TTSEngine, TTSProvider
        from core.subtitle_generator import SubtitleGenerator
        from core.broll_selector import BrollSelector
        from core.ffmpeg_composer import FFmpegComposer, load_preset
        from core.thumbnail_generator import ThumbnailGenerator
        from core.upload_packager import UploadPackager
        from moviepy import AudioFileClip

        script = ModularScript.from_json(script_dict)
        output_dir = Path(output_dir)
        assets_dir = Path(assets_dir)

        project_id = script.get_project_id()
        project_dir = output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 1. 대본 저장
        script_path = project_dir / "script.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_dict, f, ensure_ascii=False, indent=2)

        # 2. TTS 생성
        tts_text = script.to_tts_text()
        tts_path = project_dir / "audio.mp3"
        tts = TTSEngine(provider=TTSProvider.EDGE, lang="ko")
        tts.generate(tts_text, tts_path)

        # 오디오 길이 확인
        with AudioFileClip(str(tts_path)) as audio:
            duration = audio.duration

        # 3. 자막 생성
        srt_path = project_dir / "captions.srt"
        subtitle_gen = SubtitleGenerator()
        subtitle_gen.generate_from_script(tts_text, duration, srt_path)

        # 4. B-roll 선택
        selector = BrollSelector(assets_path=assets_dir)
        mood_themes = {
            "calm": ["meditation", "nature"],
            "dramatic": ["dark_cinematic", "storm_adversity"],
            "hopeful": ["sunrise_hope", "nature_epic"],
            "reflective": ["sunset_reflection", "time_passing"]
        }
        themes = mood_themes.get(script.mood, ["nature_epic"])
        themes.extend(script.broll_keywords)
        clips = selector.select(themes, duration)

        # 5. 영상 합성
        config = load_preset("v1")
        video_path = project_dir / "video.mp4"
        composer = FFmpegComposer(config=config)
        result_path, _ = composer.compose(
            audio_path=tts_path,
            broll_clips=clips,
            srt_path=srt_path,
            output_path=video_path
        )

        # 6. 썸네일 생성
        thumbnail_path = project_dir / "thumbnail.png"
        thumb_gen = ThumbnailGenerator()
        thumb_gen.generate(
            video_path=result_path,
            output_path=thumbnail_path,
            hook_text=script.s1_hook
        )

        # 7. 업로드 정보 생성
        upload_info_path = project_dir / "upload_info.txt"
        packager = UploadPackager()
        packager.generate(script_path, upload_info_path)

        return str(result_path), None

    except Exception as e:
        return None, str(e)


class BatchFactory:
    """배치 영상 생성 공장 (FFmpeg + NVENC)"""

    def __init__(self, preset: str = "v1"):
        project_root = Path(__file__).parent.parent
        self.output_dir = project_root / "output"
        self.assets_dir = project_root / "assets" / "b-roll"
        self.data_dir = project_root / "data"
        self.error_log = project_root / "output" / "errors.log"

        # preset 로드
        self.config = load_preset(preset)

        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_scripts(self, file_name: str = "scripts_pilot_20.json") -> List[ModularScript]:
        """스크립트 파일 로드"""
        file_path = self.data_dir / file_name
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [ModularScript.from_json(item) for item in data]

    def produce_one(self, script: ModularScript) -> Path:
        """단일 영상 생성 (FFmpeg + NVENC)"""
        start_time = time.time()
        project_id = script.get_project_id()
        project_dir = self.output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*50}")
        print(f"[Factory] Batch Generate - ID {script.id}")
        print(f"{'='*50}")
        print(f"[Project] {project_id}")
        print(f"[Category] {script.category}")
        print(f"[Topic] {script.topic}")
        print(f"[Mood] {script.mood}")
        print(f"[Keywords] {', '.join(script.broll_keywords)}")
        print(f"{'='*50}\n")

        # 1. 대본 저장 (V2 형식)
        script_path = project_dir / "script.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump({
                "version": script.version,
                "id": script.id,
                "category": script.category,
                "topic": script.topic,
                "mood": script.mood,
                "cta_type": script.cta_type,
                "s1_hook": script.s1_hook,
                "s2_pain": script.s2_pain,
                "s3_reframe": script.s3_reframe,
                "s4_insight": script.s4_insight,
                "s5_action": script.s5_action,
                "s6_loop_cta": script.s6_loop_cta,
                "broll_keywords": script.broll_keywords
            }, f, ensure_ascii=False, indent=2)
        print(f"[OK] 1/7 Script saved (V2)")

        # 2. TTS 생성
        tts_text = script.to_tts_text()
        tts_path = project_dir / "audio.mp3"

        tts = TTSEngine(provider=TTSProvider.EDGE, lang="ko")
        tts.generate(tts_text, tts_path)
        print(f"[OK] 2/7 TTS generated")

        # 오디오 길이 확인
        from moviepy import AudioFileClip
        with AudioFileClip(str(tts_path)) as audio:
            duration = audio.duration
        print(f"     Audio duration: {duration:.1f}s")

        # 3. 자막 생성
        srt_path = project_dir / "captions.srt"
        subtitle_gen = SubtitleGenerator()
        subtitle_gen.generate_from_script(tts_text, duration, srt_path)
        print(f"[OK] 3/7 Subtitles generated")

        # 4. B-roll 선택
        selector = BrollSelector(assets_path=self.assets_dir)

        # mood + broll_keywords로 테마 결정
        mood_themes = {
            "calm": ["meditation", "nature"],
            "dramatic": ["dark_cinematic", "storm_adversity"],
            "hopeful": ["sunrise_hope", "nature_epic"],
            "reflective": ["sunset_reflection", "time_passing"]
        }
        themes = mood_themes.get(script.mood, ["nature_epic"])
        themes.extend(script.broll_keywords)

        clips = selector.select(themes, duration)
        print(f"[OK] 4/7 B-roll selected ({len(clips)} clips)")

        # 5. 영상 합성 (FFmpeg + NVENC)
        video_path = project_dir / "video.mp4"
        composer = FFmpegComposer(config=self.config)
        result_path, compose_time = composer.compose(
            audio_path=tts_path,
            broll_clips=clips,
            srt_path=srt_path,
            output_path=video_path
        )
        print(f"[OK] 5/7 Video composed ({compose_time:.1f}s)")

        # 6. 썸네일 생성
        thumbnail_path = project_dir / "thumbnail.png"
        thumb_gen = ThumbnailGenerator()
        thumb_gen.generate(
            video_path=result_path,
            output_path=thumbnail_path,
            hook_text=script.s1_hook
        )
        print(f"[OK] 6/7 Thumbnail generated")

        # 7. 업로드 정보 생성
        upload_info_path = project_dir / "upload_info.txt"
        packager = UploadPackager()
        packager.generate(script_path, upload_info_path)
        print(f"[OK] 7/7 Upload info created")

        total_time = time.time() - start_time
        file_size = result_path.stat().st_size / 1024 / 1024

        print(f"\n{'='*50}")
        print(f"[DONE] ID {script.id} complete!")
        print(f"{'='*50}")
        print(f"업로드할 파일:")
        print(f"  video.mp4 ({file_size:.1f} MB)")
        print(f"  thumbnail.png")
        print(f"복붙용 정보:")
        print(f"  upload_info.txt")
        print(f"{'='*50}")
        print(f"[TIME] {total_time:.1f}s (compose: {compose_time:.1f}s)")
        print(f"[FOLDER] {project_dir}")
        print(f"{'='*50}\n")

        return result_path

    def _log_error(self, script_id: int, error: str):
        """에러를 errors.log에 기록"""
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.error_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] ID {script_id}: {error}\n")

    def produce_all(self, scripts: List[ModularScript], parallel: int = 0) -> List[Path]:
        """
        모든 스크립트 배치 생성 (에러 격리 + 스킵)

        Args:
            scripts: 스크립트 목록
            parallel: 병렬 워커 수 (0=순차, 1-8=병렬)
        """
        total = len(scripts)
        batch_start = time.time()

        print(f"\n{'#'*50}")
        print(f"# BATCH GENERATION - {total} videos")
        print(f"# Preset: v1 (FFmpeg + NVENC)")
        if parallel > 0:
            print(f"# Mode: PARALLEL ({parallel} workers)")
        else:
            print(f"# Mode: SEQUENTIAL")
        print(f"{'#'*50}\n")

        if parallel > 0:
            results, errors = self._produce_parallel(scripts, parallel)
        else:
            results, errors = self._produce_sequential(scripts)

        # 결과 요약
        batch_time = time.time() - batch_start
        success = sum(1 for r in results if r is not None)
        failed = len(errors)

        print(f"\n{'#'*50}")
        print(f"# BATCH COMPLETE")
        print(f"# Success: {success}/{total}")
        print(f"# Failed: {failed}/{total}")
        print(f"# Total time: {batch_time:.1f}s ({batch_time/60:.1f}min)")
        if success > 0:
            print(f"# Avg per video: {batch_time/success:.1f}s")
        if parallel > 0 and success > 0:
            print(f"# Speedup: ~{parallel}x (parallel)")
        if failed > 0:
            print(f"# Error log: {self.error_log}")
        print(f"{'#'*50}\n")

        return results

    def _produce_sequential(self, scripts: List[ModularScript]) -> Tuple[List[Path], List[Tuple[int, str]]]:
        """순차 처리"""
        results = []
        errors = []
        total = len(scripts)

        for i, script in enumerate(scripts, 1):
            print(f"\n>>> Processing {i}/{total} <<<")
            try:
                video_path = self.produce_one(script)
                results.append(video_path)
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] ID {script.id} failed: {error_msg}")
                print(f"[SKIP] Continuing to next...")
                self._log_error(script.id, error_msg)
                errors.append((script.id, error_msg))
                results.append(None)

        return results, errors

    def _produce_parallel(self, scripts: List[ModularScript], workers: int) -> Tuple[List[Path], List[Tuple[int, str]]]:
        """병렬 처리 (ProcessPoolExecutor)"""
        results = [None] * len(scripts)
        errors = []
        total = len(scripts)

        # 스크립트 데이터를 직렬화 가능한 dict로 변환
        script_dicts = []
        for s in scripts:
            script_dicts.append({
                "id": s.id,
                "category": s.category,
                "topic": s.topic,
                "mood": s.mood,
                "s1_hook": s.s1_hook,
                "s2_pain": s.s2_pain,
                "s3_reframe": s.s3_reframe,
                "s4_insight": s.s4_insight,
                "s5_action": s.s5_action,
                "s6_loop_cta": s.s6_loop_cta,
                "broll_keywords": s.broll_keywords,
                "version": s.version,
                "cta_type": s.cta_type
            })

        print(f"[PARALLEL] Starting {workers} workers for {total} videos...")

        with ProcessPoolExecutor(max_workers=workers) as executor:
            # 각 스크립트에 대한 future 생성
            future_to_idx = {
                executor.submit(_worker_produce, script_dict, str(self.output_dir), str(self.assets_dir)): idx
                for idx, script_dict in enumerate(script_dicts)
            }

            completed = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                script_id = scripts[idx].id
                completed += 1

                try:
                    result_path, error = future.result()
                    if error:
                        print(f"[{completed}/{total}] ID {script_id} FAILED: {error}")
                        self._log_error(script_id, error)
                        errors.append((script_id, error))
                    else:
                        print(f"[{completed}/{total}] ID {script_id} OK: {result_path}")
                        results[idx] = Path(result_path) if result_path else None
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{completed}/{total}] ID {script_id} EXCEPTION: {error_msg}")
                    self._log_error(script_id, error_msg)
                    errors.append((script_id, error_msg))

        return results, errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch Generate")
    parser.add_argument("--id", type=int, help="Script ID to generate (1-20)")
    parser.add_argument("--all", action="store_true", help="Generate all scripts")
    parser.add_argument("--parallel", "-p", type=int, default=0,
                        help="Number of parallel workers (0=sequential, 2-4 recommended)")
    parser.add_argument("--file", type=str, default="scripts_v2.1_examples.json",
                        help="Script file name (default: V2.1 examples)")

    args = parser.parse_args()

    # 병렬 워커 수 제한 (GPU 메모리 고려)
    if args.parallel > 8:
        print(f"[WARN] Reducing workers from {args.parallel} to 8 (max)")
        args.parallel = 8

    factory = BatchFactory()
    scripts = factory.load_scripts(args.file)

    if args.id:
        # 특정 ID만 생성
        script = next((s for s in scripts if s.id == args.id), None)
        if script:
            video_path = factory.produce_one(script)
            print(f"\n[COMPLETE] {video_path}")
        else:
            print(f"[ERROR] Script ID {args.id} not found")
    elif args.all:
        # 전체 생성 (순차 또는 병렬)
        factory.produce_all(scripts, parallel=args.parallel)
    else:
        print("Usage:")
        print("  python batch_generate.py --id 1              # Single video")
        print("  python batch_generate.py --all               # All videos (sequential)")
        print("  python batch_generate.py --all --parallel 4  # All videos (4 workers)")


if __name__ == "__main__":
    main()
