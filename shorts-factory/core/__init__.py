"""
Shorts Factory - Core Modules
유튜브 쇼츠 자동 생성 파이프라인
"""

from .quote_loader import QuoteLoader, Quote
from .script_generator import ScriptGenerator, Script, HookType, CTAType
from .review_loop import ReviewLoop, ReviewResult
from .tts_engine import TTSEngine, TTSProvider, TTSError, get_audio_duration
from .subtitle_generator import SubtitleGenerator, SubtitleEntry, SubtitleConfig
from .broll_selector import BrollSelector, BrollClip, BrollConfig
from .video_composer import VideoComposer, CompositionConfig
from .metadata_generator import MetadataGenerator, VideoMetadata

__all__ = [
    # Quote
    'QuoteLoader',
    'Quote',
    # Script
    'ScriptGenerator',
    'Script',
    'HookType',
    'CTAType',
    # Review
    'ReviewLoop',
    'ReviewResult',
    # TTS
    'TTSEngine',
    'TTSProvider',
    'TTSError',
    'get_audio_duration',
    # Subtitle
    'SubtitleGenerator',
    'SubtitleEntry',
    'SubtitleConfig',
    # B-roll
    'BrollSelector',
    'BrollClip',
    'BrollConfig',
    # Video
    'VideoComposer',
    'CompositionConfig',
    # Metadata
    'MetadataGenerator',
    'VideoMetadata',
]

__version__ = '0.2.0'
