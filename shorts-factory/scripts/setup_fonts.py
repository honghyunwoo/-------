"""
Font Setup for Shorts Factory
한글 폰트 다운로드 및 설정

사용법:
    python scripts/setup_fonts.py
    python scripts/setup_fonts.py --check
"""

import os
import sys
import json
import zipfile
import requests
import argparse
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

# Google Fonts 다운로드 URL
FONT_SOURCES = {
    "NotoSansKR": {
        "url": "https://fonts.google.com/download?family=Noto%20Sans%20KR",
        "description": "Google Noto Sans KR (한글 기본 폰트)",
        "files": ["NotoSansKR-Regular.ttf", "NotoSansKR-Bold.ttf", "NotoSansKR-Medium.ttf"]
    },
    "NotoSerifKR": {
        "url": "https://fonts.google.com/download?family=Noto%20Serif%20KR",
        "description": "Google Noto Serif KR (명언용 세리프 폰트)",
        "files": ["NotoSerifKR-Regular.ttf", "NotoSerifKR-Bold.ttf", "NotoSerifKR-Medium.ttf"]
    }
}

# Windows 시스템 폰트 경로
WINDOWS_FONT_PATHS = [
    Path("C:/Windows/Fonts/malgun.ttf"),  # 맑은 고딕
    Path("C:/Windows/Fonts/malgunbd.ttf"),  # 맑은 고딕 Bold
    Path("C:/Windows/Fonts/NanumGothic.ttf"),  # 나눔고딕
    Path("C:/Windows/Fonts/NanumGothicBold.ttf"),  # 나눔고딕 Bold
]


def check_system_fonts() -> dict:
    """시스템에 설치된 한글 폰트 확인"""
    available = {}
    for font_path in WINDOWS_FONT_PATHS:
        if font_path.exists():
            available[font_path.stem] = str(font_path)
    return available


def check_project_fonts() -> dict:
    """프로젝트에 설치된 폰트 확인"""
    available = {}
    if FONTS_DIR.exists():
        for font_file in FONTS_DIR.glob("*.ttf"):
            available[font_file.stem] = str(font_file)
        for font_file in FONTS_DIR.glob("*.otf"):
            available[font_file.stem] = str(font_file)
    return available


def download_google_font(font_name: str) -> bool:
    """Google Fonts에서 폰트 다운로드"""
    if font_name not in FONT_SOURCES:
        print(f"[ERROR] Unknown font: {font_name}")
        return False

    config = FONT_SOURCES[font_name]
    url = config["url"]

    print(f"\n[DOWNLOAD] {font_name}")
    print(f"  {config['description']}")

    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FONTS_DIR / f"{font_name}.zip"

    try:
        print(f"  Downloading from Google Fonts...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for file in zf.namelist():
                if file.endswith(('.ttf', '.otf')):
                    # 파일명만 추출
                    filename = Path(file).name
                    with zf.open(file) as src, open(FONTS_DIR / filename, 'wb') as dst:
                        dst.write(src.read())
                    print(f"    Extracted: {filename}")

        # ZIP 파일 삭제
        zip_path.unlink()
        print(f"  [OK] {font_name} installed")
        return True

    except Exception as e:
        print(f"  [ERROR] Download failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return False


def create_font_config():
    """폰트 설정 파일 생성"""
    config = {
        "system_fonts": check_system_fonts(),
        "project_fonts": check_project_fonts(),
        "recommended": {}
    }

    # 추천 폰트 설정
    all_fonts = {**config["system_fonts"], **config["project_fonts"]}

    # 자막용 (sans-serif)
    for name in ["NotoSansKR-Bold", "malgunbd", "NanumGothicBold", "NotoSansKR-Regular", "malgun"]:
        if name in all_fonts:
            config["recommended"]["subtitle"] = all_fonts[name]
            break

    # 명언용 (serif or bold)
    for name in ["NotoSerifKR-Bold", "NotoSerifKR-Medium", "NotoSansKR-Bold"]:
        if name in all_fonts:
            config["recommended"]["quote"] = all_fonts[name]
            break

    # 일반 텍스트
    for name in ["NotoSansKR-Regular", "malgun", "NanumGothic"]:
        if name in all_fonts:
            config["recommended"]["text"] = all_fonts[name]
            break

    # 설정 파일 저장
    config_path = FONTS_DIR / "font_config.json"
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def main():
    parser = argparse.ArgumentParser(description="Font Setup for Shorts Factory")
    parser.add_argument("--check", action="store_true", help="Check available fonts")
    parser.add_argument("--download", type=str, help="Download specific font (NotoSansKR, NotoSerifKR)")
    parser.add_argument("--all", action="store_true", help="Download all fonts")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Font Setup for Shorts Factory")
    print(f"{'='*60}")

    # 현재 상태 확인
    system_fonts = check_system_fonts()
    project_fonts = check_project_fonts()

    print(f"\n[System Fonts]")
    if system_fonts:
        for name, path in system_fonts.items():
            print(f"  [OK] {name}: {path}")
    else:
        print(f"  No Korean fonts found in system")

    print(f"\n[Project Fonts] ({FONTS_DIR})")
    if project_fonts:
        for name, path in project_fonts.items():
            print(f"  [OK] {name}")
    else:
        print(f"  No fonts in project folder")

    if args.check:
        config = create_font_config()
        print(f"\n[Recommended Fonts]")
        for usage, path in config.get("recommended", {}).items():
            print(f"  {usage}: {Path(path).name}")
        return

    # 다운로드
    if args.download:
        download_google_font(args.download)
    elif args.all:
        for font_name in FONT_SOURCES.keys():
            download_google_font(font_name)
    else:
        # 기본: 필요한 폰트만 다운로드
        all_fonts = {**system_fonts, **project_fonts}

        # NotoSansKR이 없으면 다운로드
        has_noto_sans = any("NotoSansKR" in name for name in all_fonts.keys())
        if not has_noto_sans:
            print("\n[INFO] Downloading NotoSansKR (recommended for subtitles)...")
            download_google_font("NotoSansKR")
        else:
            print("\n[INFO] NotoSansKR already available")

    # 설정 파일 생성
    config = create_font_config()
    print(f"\n[Config] Font configuration saved to: {FONTS_DIR / 'font_config.json'}")

    print(f"\n[Recommended Fonts]")
    for usage, path in config.get("recommended", {}).items():
        print(f"  {usage}: {Path(path).name}")

    print(f"\n{'='*60}")
    print(f"  Setup Complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
