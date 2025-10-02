import os
import shutil
import socket

import toml
from loguru import logger
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일)
load_dotenv()

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_file = f"{root_dir}/config.toml"


def load_config():
    # 수정: 설정 파일이 디렉토리인 경우 처리
    if os.path.isdir(config_file):
        shutil.rmtree(config_file)

    if not os.path.isfile(config_file):
        example_file = f"{root_dir}/config.example.toml"
        if os.path.isfile(example_file):
            shutil.copyfile(example_file, config_file)
            logger.info("copy config.example.toml to config.toml")

    logger.info(f"load config from file: {config_file}")

    try:
        _config_ = toml.load(config_file)
    except Exception as e:
        logger.warning(f"load config failed: {str(e)}, try to load as utf-8-sig")
        with open(config_file, mode="r", encoding="utf-8-sig") as fp:
            _cfg_content = fp.read()
            _config_ = toml.loads(_cfg_content)

    # 환경 변수로 민감한 설정 오버라이드 (보안 강화)
    _config_ = apply_env_overrides(_config_)
    return _config_


def apply_env_overrides(config):
    """
    환경 변수로 민감한 설정을 오버라이드합니다.
    .env 파일의 값이 config.toml보다 우선순위가 높습니다.
    """
    app = config.get("app", {})

    # API 키 오버라이드
    if os.getenv("PEXELS_API_KEY"):
        app["pexels_api_keys"] = [os.getenv("PEXELS_API_KEY")]
        logger.info("✓ Using PEXELS_API_KEY from environment variable")

    if os.getenv("PIXABAY_API_KEY"):
        app["pixabay_api_keys"] = [os.getenv("PIXABAY_API_KEY")]
        logger.info("✓ Using PIXABAY_API_KEY from environment variable")

    if os.getenv("OPENAI_API_KEY"):
        app["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        logger.info("✓ Using OPENAI_API_KEY from environment variable")

    if os.getenv("AZURE_API_KEY"):
        app["azure_api_key"] = os.getenv("AZURE_API_KEY")
        logger.info("✓ Using AZURE_API_KEY from environment variable")

    if os.getenv("GEMINI_API_KEY"):
        app["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
        logger.info("✓ Using GEMINI_API_KEY from environment variable")

    if os.getenv("YOUTUBE_API_KEY"):
        youtube_config = config.get("youtube", {})
        youtube_config["api_key"] = os.getenv("YOUTUBE_API_KEY")
        config["youtube"] = youtube_config
        logger.info("✓ Using YOUTUBE_API_KEY from environment variable")

    # Azure TTS 키 오버라이드
    azure = config.get("azure", {})
    if os.getenv("AZURE_SPEECH_KEY"):
        azure["speech_key"] = os.getenv("AZURE_SPEECH_KEY")
        logger.info("✓ Using AZURE_SPEECH_KEY from environment variable")

    if os.getenv("AZURE_SPEECH_REGION"):
        azure["speech_region"] = os.getenv("AZURE_SPEECH_REGION")
        logger.info("✓ Using AZURE_SPEECH_REGION from environment variable")

    config["azure"] = azure

    # JWT Secret 오버라이드 (보안 최우선)
    auth = config.get("auth", {})
    if os.getenv("JWT_SECRET_KEY"):
        auth["secret_key"] = os.getenv("JWT_SECRET_KEY")
        logger.info("✓ Using JWT_SECRET_KEY from environment variable")

    config["auth"] = auth
    config["app"] = app

    return config


def save_config():
    with open(config_file, "w", encoding="utf-8") as f:
        _cfg["app"] = app
        _cfg["azure"] = azure
        _cfg["siliconflow"] = siliconflow
        _cfg["ui"] = ui
        _cfg["database"] = database
        _cfg["auth"] = auth
        f.write(toml.dumps(_cfg))


_cfg = load_config()
app = _cfg.get("app", {})
whisper = _cfg.get("whisper", {})
proxy = _cfg.get("proxy", {})
azure = _cfg.get("azure", {})
siliconflow = _cfg.get("siliconflow", {})
database = _cfg.get("database", {})
auth = _cfg.get("auth", {})
ui = _cfg.get(
    "ui",
    {
        "hide_log": False,
    },
)

hostname = socket.gethostname()

log_level = _cfg.get("log_level", "DEBUG")
listen_host = _cfg.get("listen_host", "0.0.0.0")
listen_port = _cfg.get("listen_port", 8080)
project_name = _cfg.get("project_name", "올빼미 AI 영상 스튜디오")
project_description = _cfg.get(
    "project_description",
    "AI 기반 자동 영상 제작 플랫폼 - 24시간 함께하는 프리미엄 영상 제작 서비스",
)
project_version = _cfg.get("project_version", "1.0.0")
reload_debug = False

imagemagick_path = app.get("imagemagick_path", "")
if imagemagick_path and os.path.isfile(imagemagick_path):
    os.environ["IMAGEMAGICK_BINARY"] = imagemagick_path

ffmpeg_path = app.get("ffmpeg_path", "")
if ffmpeg_path and os.path.isfile(ffmpeg_path):
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path

logger.info(f"{project_name} v{project_version}")

# Config 객체 생성 (프로그램 전체 설정 관리)
class Config:
    def __init__(self):
        self.project_name = project_name
        self.project_description = project_description
        self.project_version = project_version
        self.log_level = log_level
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.reload_debug = reload_debug
        # 설정 데이터 저장 (앱 전체에서 사용)
        self.app = app
        self.whisper = whisper
        self.proxy = proxy
        self.azure = azure
        self.siliconflow = siliconflow
        self.database = database
        self.auth = auth
        self.ui = ui

config = Config()
