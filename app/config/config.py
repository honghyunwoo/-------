import os
import shutil
import socket

import toml
from loguru import logger

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
    return _config_


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
