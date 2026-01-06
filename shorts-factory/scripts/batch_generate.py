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
from typing import List

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tts_engine import TTSEngine, TTSProvider
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector
from core.video_composer import VideoComposer


@dataclass
class ModularScript:
    """6문장 형식 스크립트"""
    id: int
    category: str
    topic: str
    mood: str
    s1_hook: str
    s2_pain: str
    s3_insight: str
    s4_action: str
    s5_result: str
    s6_loop_cta: str
    broll_keywords: List[str]

    @classmethod
    def from_json(cls, data: dict) -> 'ModularScript':
        return cls(
            id=data.get("id", 0),
            category=data.get("category", ""),
            topic=data.get("topic", ""),
            mood=data.get("mood", "dramatic"),
            s1_hook=data.get("s1_hook", ""),
            s2_pain=data.get("s2_pain", ""),
            s3_insight=data.get("s3_insight", ""),
            s4_action=data.get("s4_action", ""),
            s5_result=data.get("s5_result", ""),
            s6_loop_cta=data.get("s6_loop_cta", ""),
            broll_keywords=data.get("broll_keywords", [])
        )

    def to_tts_text(self) -> str:
        """TTS용 텍스트 - 6문장 순서대로"""
        sentences = [
            self.s1_hook,
            self.s2_pain,
            self.s3_insight,
            self.s4_action,
            self.s5_result,
            self.s6_loop_cta
        ]
        return " ".join(s for s in sentences if s)

    def get_project_id(self) -> str:
        """프로젝트 ID 생성"""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{date_str}_{self.category}_{self.id:02d}"


class BatchFactory:
    """배치 영상 생성 공장"""

    def __init__(self):
        project_root = Path(__file__).parent.parent
        self.output_dir = project_root / "output"
        self.assets_dir = project_root / "assets" / "b-roll"
        self.data_dir = project_root / "data"

    def load_scripts(self, file_name: str = "scripts_pilot_20.json") -> List[ModularScript]:
        """스크립트 파일 로드"""
        file_path = self.data_dir / file_name
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [ModularScript.from_json(item) for item in data]

    def produce_one(self, script: ModularScript) -> Path:
        """단일 영상 생성"""
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

        # 1. 대본 저장
        script_path = project_dir / "script.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump({
                "id": script.id,
                "category": script.category,
                "topic": script.topic,
                "mood": script.mood,
                "s1_hook": script.s1_hook,
                "s2_pain": script.s2_pain,
                "s3_insight": script.s3_insight,
                "s4_action": script.s4_action,
                "s5_result": script.s5_result,
                "s6_loop_cta": script.s6_loop_cta,
                "broll_keywords": script.broll_keywords
            }, f, ensure_ascii=False, indent=2)
        print(f"[OK] 1/5 Script saved")

        # 2. TTS 생성
        tts_text = script.to_tts_text()
        tts_path = project_dir / "audio.mp3"

        tts = TTSEngine(provider=TTSProvider.EDGE, lang="ko")
        tts.generate(tts_text, tts_path)
        print(f"[OK] 2/5 TTS generated")

        # 오디오 길이 확인
        from moviepy import AudioFileClip
        with AudioFileClip(str(tts_path)) as audio:
            duration = audio.duration
        print(f"     Audio duration: {duration:.1f}s")

        # 3. 자막 생성
        srt_path = project_dir / "captions.srt"
        subtitle_gen = SubtitleGenerator()
        subtitle_gen.generate_from_script(tts_text, duration, srt_path)
        print(f"[OK] 3/5 Subtitles generated")

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
        print(f"[OK] 4/5 B-roll selected ({len(clips)} clips)")

        # 5. 영상 합성
        video_path = project_dir / "video.mp4"
        composer = VideoComposer()
        composer.compose(
            audio_path=tts_path,
            broll_clips=clips,
            srt_path=srt_path,
            output_path=video_path
        )
        print(f"[OK] 5/5 Video composed")

        print(f"\n{'='*50}")
        print(f"[DONE] ID {script.id} complete!")
        print(f"[VIDEO] {video_path}")
        print(f"{'='*50}\n")

        return video_path

    def produce_all(self, scripts: List[ModularScript]) -> List[Path]:
        """모든 스크립트 배치 생성"""
        results = []
        total = len(scripts)

        print(f"\n{'#'*50}")
        print(f"# BATCH GENERATION - {total} videos")
        print(f"{'#'*50}\n")

        for i, script in enumerate(scripts, 1):
            print(f"\n>>> Processing {i}/{total} <<<")
            try:
                video_path = self.produce_one(script)
                results.append(video_path)
            except Exception as e:
                print(f"[ERROR] ID {script.id} failed: {e}")
                results.append(None)

        # 결과 요약
        success = sum(1 for r in results if r is not None)
        print(f"\n{'#'*50}")
        print(f"# BATCH COMPLETE")
        print(f"# Success: {success}/{total}")
        print(f"{'#'*50}\n")

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch Generate")
    parser.add_argument("--id", type=int, help="Script ID to generate (1-20)")
    parser.add_argument("--all", action="store_true", help="Generate all scripts")
    parser.add_argument("--file", type=str, default="scripts_pilot_20.json", help="Script file name")

    args = parser.parse_args()

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
        # 전체 생성
        factory.produce_all(scripts)
    else:
        print("Usage: python batch_generate.py --id 1")
        print("       python batch_generate.py --all")


if __name__ == "__main__":
    main()
