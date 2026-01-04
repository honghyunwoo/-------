"""
파이프라인 오케스트레이터
전체 영상 생성 프로세스 조율
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import yaml
from dotenv import load_dotenv

from core.quote_loader import QuoteLoader, Quote
from core.script_generator import ScriptGenerator, Script, HookType, CTAType
from core.review_loop import ReviewLoop
from core.tts_engine import TTSEngine, TTSProvider, get_audio_duration
from core.subtitle_generator import SubtitleGenerator
from core.broll_selector import BrollSelector, BrollClip
from core.video_composer import VideoComposer, CompositionConfig
from core.metadata_generator import MetadataGenerator, VideoMetadata


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    # 경로
    base_dir: Path = field(default_factory=lambda: Path("."))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    assets_dir: Path = field(default_factory=lambda: Path("./assets"))
    templates_dir: Path = field(default_factory=lambda: Path("./templates"))
    config_dir: Path = field(default_factory=lambda: Path("./config"))

    # API 키
    anthropic_api_key: str = ""
    typecast_api_key: str = ""
    elevenlabs_api_key: str = ""

    # 채널 설정
    channel: str = "stoic"
    language: str = "ko"
    tts_provider: TTSProvider = TTSProvider.TYPECAST
    tts_voice_id: str = ""

    # 파이프라인 설정
    review_min_score: float = 8.0
    review_max_iterations: int = 3
    default_hook_type: str = "H1"
    default_cta_type: str = "C3"

    # 영상 설정
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    bgm_volume: float = 0.2

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'PipelineConfig':
        """YAML에서 설정 로드"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        config = cls()

        # 경로 설정
        paths = data.get('paths', {})
        config.output_dir = Path(paths.get('output', './output'))
        config.assets_dir = Path(paths.get('assets', './assets'))
        config.templates_dir = Path(paths.get('templates', './templates'))

        # 파이프라인 설정
        pipeline = data.get('pipeline', {})
        config.review_min_score = pipeline.get('review_min_score', 8.0)
        config.review_max_iterations = pipeline.get('review_max_iterations', 3)
        config.default_hook_type = pipeline.get('default_hook_type', 'H1')
        config.default_cta_type = pipeline.get('default_cta_type', 'C3')

        # 영상 설정
        video = data.get('video', {})
        config.video_width = video.get('width', 1080)
        config.video_height = video.get('height', 1920)
        config.video_fps = video.get('fps', 30)

        # BGM 설정
        bgm = data.get('bgm', {})
        config.bgm_volume = bgm.get('volume', 0.2)

        # 채널 설정
        channels = data.get('channels', {})
        if config.channel in channels:
            ch = channels[config.channel]
            config.language = ch.get('language', 'ko')
            tts_provider = ch.get('tts_provider', 'typecast')
            config.tts_provider = TTSProvider(tts_provider)
            config.tts_voice_id = ch.get('tts_voice_id', '')

        return config

    def load_env(self):
        """환경 변수에서 API 키 로드"""
        load_dotenv(self.config_dir / '.env')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.typecast_api_key = os.getenv('TYPECAST_API_KEY', '')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', '')


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    srt_path: Optional[Path] = None
    metadata_path: Optional[Path] = None
    script: Optional[Script] = None
    quote: Optional[Quote] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    output_dir: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "video_path": str(self.video_path) if self.video_path else None,
            "audio_path": str(self.audio_path) if self.audio_path else None,
            "srt_path": str(self.srt_path) if self.srt_path else None,
            "metadata_path": str(self.metadata_path) if self.metadata_path else None,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "output_dir": str(self.output_dir) if self.output_dir else None
        }


class Pipeline:
    """Shorts Factory 파이프라인"""

    def __init__(self, config: PipelineConfig = None, config_path: Path = None):
        if config_path:
            self.config = PipelineConfig.from_yaml(config_path)
        else:
            self.config = config or PipelineConfig()

        self.config.load_env()
        self._init_modules()

    def _init_modules(self):
        """모듈 초기화"""
        # 명언 로더
        quotes_path = self.config.templates_dir / self.config.channel / "quotes_library.json"
        self.quote_loader = QuoteLoader(str(quotes_path))

        # 스크립트 생성기
        prompts_path = self.config.templates_dir / self.config.channel / "prompts.yaml"

        self.script_generator = ScriptGenerator(
            api_key=self.config.anthropic_api_key,
            prompts_path=str(prompts_path)
        )

        # 재검토 루프
        self.review_loop = ReviewLoop(
            api_key=self.config.anthropic_api_key,
            prompts_path=str(prompts_path),
            min_score=self.config.review_min_score,
            max_iterations=self.config.review_max_iterations
        )

        # TTS 엔진
        tts_api_key = (
            self.config.typecast_api_key
            if self.config.tts_provider == TTSProvider.TYPECAST
            else self.config.elevenlabs_api_key
        )
        self.tts_engine = TTSEngine(
            provider=self.config.tts_provider,
            api_key=tts_api_key,
            voice_id=self.config.tts_voice_id
        )

        # 자막 생성기
        self.subtitle_gen = SubtitleGenerator()

        # B-roll 선택기
        broll_path = self.config.assets_dir / "b-roll"
        self.broll_selector = BrollSelector(assets_path=broll_path)

        # 영상 합성기
        composition_config = CompositionConfig(
            width=self.config.video_width,
            height=self.config.video_height,
            fps=self.config.video_fps,
            bgm_volume=self.config.bgm_volume
        )
        self.video_composer = VideoComposer(config=composition_config)

        # 메타데이터 생성기
        self.metadata_gen = MetadataGenerator(
            api_key=self.config.anthropic_api_key
        )

    def run(
        self,
        quote_id: int,
        hook_type: str = None,
        cta_type: str = None,
        skip_tts: bool = False,
        skip_video: bool = False,
        skip_review: bool = False,
        use_api: bool = True,
        bgm_path: Path = None
    ) -> PipelineResult:
        """파이프라인 실행"""
        start_time = datetime.now()
        hook_type = hook_type or self.config.default_hook_type
        cta_type = cta_type or self.config.default_cta_type

        # API 키가 없으면 자동으로 API 사용 안함
        if not self.config.anthropic_api_key:
            use_api = False
            skip_review = True

        # 출력 디렉토리 생성
        output_dir = self._create_output_dir(quote_id)

        try:
            # 1. 명언 로드
            logger.info(f"[1/8] 명언 로드 중... (ID: {quote_id})")
            quote = self.quote_loader.get_by_id(quote_id)
            logger.info(f"  → {quote.text[:30]}...")

            # 2. 스크립트 생성
            logger.info(f"[2/8] 스크립트 생성 중... (훅: {hook_type}, CTA: {cta_type})")
            if use_api:
                script = self.script_generator.generate(quote, hook_type, cta_type)
            else:
                logger.info("  → API 없이 템플릿 기반 생성")
                script = self.script_generator.generate_simple(quote, hook_type, cta_type)
            logger.info(f"  → 스크립트 생성 완료")

            # 스크립트 저장
            script_path = output_dir / "script.json"
            self._save_script(script, script_path)

            # 3. 재검토 루프
            if not skip_review and use_api:
                logger.info(f"[3/8] 스크립트 품질 검토 중...")
                script = self.review_loop.review_and_improve(script)
                logger.info(f"  → 최종 점수: {script.review_score:.1f}/10")
            else:
                logger.info(f"[3/8] 스크립트 검토 건너뜀")
                script.review_score = 8.0  # 기본 점수

            # 개선된 스크립트 저장
            self._save_script(script, script_path)

            # TTS 텍스트 저장
            tts_text_path = output_dir / "tts_text.txt"
            with open(tts_text_path, 'w', encoding='utf-8') as f:
                f.write(script.full_text)

            audio_path = None
            srt_path = None
            video_path = None

            if not skip_tts:
                # 4. TTS 생성
                logger.info(f"[4/8] TTS 음성 생성 중...")
                audio_path = output_dir / "audio.mp3"
                self.tts_engine.generate(script.full_text, audio_path)
                audio_duration = get_audio_duration(audio_path)
                logger.info(f"  → 음성 생성 완료 ({audio_duration:.1f}초)")

                # 5. 자막 생성
                logger.info(f"[5/8] 자막 생성 중...")
                srt_path = output_dir / "captions.srt"
                self.subtitle_gen.generate_from_script(
                    script.full_text,
                    audio_duration,
                    srt_path
                )
                logger.info(f"  → 자막 생성 완료")

                if not skip_video:
                    # 6. B-roll 선택
                    logger.info(f"[6/8] B-roll 선택 중...")
                    themes = quote.themes if hasattr(quote, 'themes') else []
                    broll_clips = self.broll_selector.select(themes, audio_duration)
                    logger.info(f"  → {len(broll_clips)}개 클립 선택")

                    # 7. 영상 합성
                    logger.info(f"[7/8] 영상 합성 중...")
                    video_path = output_dir / "video.mp4"

                    # BGM 선택
                    if bgm_path is None:
                        bgm_path = self._select_bgm()

                    self.video_composer.compose(
                        audio_path=audio_path,
                        broll_clips=broll_clips,
                        srt_path=srt_path,
                        bgm_path=bgm_path,
                        output_path=video_path
                    )
                    logger.info(f"  → 영상 합성 완료")
            else:
                logger.info("[4-7] TTS/영상 생성 건너뜀")

            # 8. 메타데이터 생성
            logger.info(f"[8/8] 메타데이터 생성 중...")
            metadata = self.metadata_gen.generate(script, quote, self.config.channel)
            metadata_path = output_dir / "metadata.json"
            self.metadata_gen.save(metadata, metadata_path)
            logger.info(f"  → 메타데이터 생성 완료")

            # 명언 사용 표시
            self.quote_loader.mark_used(quote_id)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"\n✅ 파이프라인 완료! (소요시간: {duration:.1f}초)")
            logger.info(f"   출력 폴더: {output_dir}")

            return PipelineResult(
                success=True,
                video_path=video_path,
                audio_path=audio_path,
                srt_path=srt_path,
                metadata_path=metadata_path,
                script=script,
                quote=quote,
                duration_seconds=duration,
                output_dir=output_dir
            )

        except Exception as e:
            logger.error(f"❌ 파이프라인 오류: {e}")
            import traceback
            traceback.print_exc()

            return PipelineResult(
                success=False,
                error=str(e),
                output_dir=output_dir
            )

    def run_batch(
        self,
        quote_ids: List[int],
        hook_type: str = None,
        cta_type: str = None,
        **kwargs
    ) -> List[PipelineResult]:
        """배치 실행"""
        results = []
        total = len(quote_ids)

        for i, quote_id in enumerate(quote_ids, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"배치 진행: {i}/{total} (Quote ID: {quote_id})")
            logger.info(f"{'='*50}")

            result = self.run(quote_id, hook_type, cta_type, **kwargs)
            results.append(result)

        # 요약
        success_count = sum(1 for r in results if r.success)
        logger.info(f"\n{'='*50}")
        logger.info(f"배치 완료: {success_count}/{total} 성공")
        logger.info(f"{'='*50}")

        return results

    def _create_output_dir(self, quote_id: int) -> Path:
        """출력 디렉토리 생성"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        dir_name = f"{date_str}_quote_{quote_id}"
        output_dir = self.config.output_dir / dir_name

        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_script(self, script: Script, path: Path):
        """스크립트 저장"""
        import json
        data = {
            "id": script.id,
            "quote_id": script.quote_id,
            "hook": script.hook,
            "quote_text": script.quote_text,
            "explanation": script.explanation,
            "example": script.example,
            "cta": script.cta,
            "full_text": script.full_text,
            "hook_type": script.hook_type,
            "cta_type": script.cta_type,
            "review_score": script.review_score
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _select_bgm(self) -> Optional[Path]:
        """BGM 선택"""
        bgm_dir = self.config.assets_dir / "bgm"
        if not bgm_dir.exists():
            return None

        bgm_files = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        if bgm_files:
            import random
            return random.choice(bgm_files)
        return None


def create_pipeline(config_path: str = None) -> Pipeline:
    """파이프라인 팩토리 함수"""
    if config_path:
        return Pipeline(config_path=Path(config_path))
    else:
        default_config = Path("config/settings.yaml")
        if default_config.exists():
            return Pipeline(config_path=default_config)
        return Pipeline()


if __name__ == "__main__":
    # 테스트 실행
    pipeline = create_pipeline()
    result = pipeline.run(quote_id=1, skip_tts=True, skip_video=True)
    print(result.to_dict())
