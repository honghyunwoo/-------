"""
Shorts Factory - 공장 모드
대본 JSON을 받아서 영상을 자동 생성합니다.

사용법:
    python scripts/factory.py --script "JSON 대본"
    python scripts/factory.py --file script.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tts_engine import TTSEngine, TTSProvider
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector
from core.video_composer import VideoComposer


@dataclass
class Script:
    """대본 데이터"""
    hook: str
    quote: str
    author: str
    explanation: str
    application: str
    cta: str
    keywords: list
    mood: str = "calm"

    @classmethod
    def from_json(cls, data: dict) -> 'Script':
        return cls(
            hook=data.get("hook", ""),
            quote=data.get("quote", ""),
            author=data.get("author", ""),
            explanation=data.get("explanation", ""),
            application=data.get("application", ""),
            cta=data.get("cta", ""),
            keywords=data.get("keywords", []),
            mood=data.get("mood", "calm")
        )

    def to_tts_text(self) -> str:
        """TTS용 텍스트 생성 - 각 섹션을 문장으로 구분"""
        parts = [
            self.hook,
            f'{self.quote}. {self.author}.',  # 명언과 저자를 별도 문장으로
            self.explanation,
            self.application,
            self.cta
        ]
        return " ".join(p for p in parts if p)


class ShortsFactory:
    """Shorts 영상 공장"""

    def __init__(self, output_dir: Path = None):
        # 프로젝트 루트 기준 절대 경로 사용
        project_root = Path(__file__).parent.parent
        self.output_dir = Path(output_dir) if output_dir else project_root / "output"
        self.assets_dir = project_root / "assets" / "b-roll"

    def produce(self, script: Script, project_id: str = None) -> Path:
        """영상 생산 (동기)"""
        # 프로젝트 ID 생성
        if not project_id:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            project_id = f"{timestamp}_shorts"

        project_dir = self.output_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*50}")
        print(f"[Factory] Shorts Factory - Start")
        print(f"{'='*50}")
        print(f"[Project] {project_id}")
        print(f"[Mood] {script.mood}")
        print(f"[Keywords] {', '.join(script.keywords)}")
        print(f"{'='*50}\n")

        # 1. 대본 저장
        script_path = project_dir / "script.json"
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump({
                "hook": script.hook,
                "quote": script.quote,
                "author": script.author,
                "explanation": script.explanation,
                "application": script.application,
                "cta": script.cta,
                "keywords": script.keywords,
                "mood": script.mood
            }, f, ensure_ascii=False, indent=2)
        print(f"[OK] 1/5 Script saved")

        # 2. TTS 생성 (무료 Edge TTS 사용)
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

        # mood에 따른 테마 매핑
        mood_themes = {
            "calm": ["마음", "자연"],
            "dramatic": ["역경", "시간"],
            "hopeful": ["행복", "미덕"],
            "reflective": ["마음", "시간"]
        }
        themes = mood_themes.get(script.mood, ["자연"])
        themes.extend(script.keywords[:2])  # 키워드도 추가

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
        print(f"[DONE] Production complete!")
        print(f"[VIDEO] {video_path}")
        print(f"{'='*50}\n")

        return video_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Shorts Factory")
    parser.add_argument("--script", type=str, help="JSON script")
    parser.add_argument("--file", type=str, help="JSON file path")
    parser.add_argument("--id", type=str, help="Project ID")

    args = parser.parse_args()

    # 대본 로드
    if args.script:
        script_data = json.loads(args.script)
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
    else:
        # 예시 대본
        script_data = {
            "hook": "왜 2000년 전 황제의 일기가 오늘도 읽힐까요?",
            "quote": "장애물이 곧 길이 된다.",
            "author": "마르쿠스 아우렐리우스",
            "explanation": "우리 앞의 장애물은 피해야 할 대상이 아닙니다. 그것을 통과하며 우리는 성장합니다. 역경이 최고의 스승인 이유입니다.",
            "application": "오늘 겪는 어려움을 기회로 바꿔보세요. 그 안에 답이 있습니다.",
            "cta": "더 많은 지혜가 필요하다면 구독하세요.",
            "keywords": ["obstacle", "stoic", "growth"],
            "mood": "dramatic"
        }
        print("[INFO] Running with example script...")

    script = Script.from_json(script_data)
    factory = ShortsFactory()

    video_path = factory.produce(script, args.id)
    print(f"\n[COMPLETE] {video_path}")


if __name__ == "__main__":
    main()
