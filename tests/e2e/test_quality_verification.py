import os
import json
import subprocess
from pathlib import Path
from loguru import logger

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = ROOT_DIR / "storage" / "tasks"
REPORT_PATH = STORAGE_DIR / "quality_verification_report.json"

def get_video_properties(video_path: Path) -> dict:
    """ffprobe를 사용하여 비디오 속성 추출"""
    if not video_path.exists():
        return {"error": "File not found"}

    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,bit_rate,duration",
        "-of", "json",
        str(video_path)
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        properties = json.loads(result.stdout)["streams"][0]

        # 프레임 레이트 계산
        r_frame_rate = properties.get("r_frame_rate", "0/1").split('/')
        if len(r_frame_rate) == 2 and int(r_frame_rate[1]) != 0:
            fps = float(r_frame_rate[0]) / float(r_frame_rate[1])
        else:
            fps = 0

        return {
            "width": int(properties.get("width", 0)),
            "height": int(properties.get("height", 0)),
            "fps": round(fps, 2),
            "bit_rate_kbps": round(int(properties.get("bit_rate", 0)) / 1000, 2),
            "duration_seconds": float(properties.get("duration", 0)),
            "file_size_mb": round(video_path.stat().st_size / (1024 * 1024), 2)
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError, KeyError) as e:
        logger.error(f"Error processing {video_path}: {e}")
        return {"error": str(e)}

def verify_quality():
    """
    모든 생성된 영상의 품질을 검증하고 리포트를 생성합니다.
    """
    logger.info("Starting quality verification for all generated videos...")
    report = {
        "verification_date": datetime.now().isoformat(),
        "videos": []
    }

    if not STORAGE_DIR.exists():
        logger.warning(f"Storage directory not found: {STORAGE_DIR}")
        return

    video_files = list(STORAGE_DIR.glob("**/final-*.mp4"))
    logger.info(f"Found {len(video_files)} videos to verify.")

    for video_path in video_files:
        properties = get_video_properties(video_path)
        
        # 검증 로직
        is_bitrate_ok = properties.get("bit_rate_kbps", 0) >= 7000  # 8000k 목표, 7000k 이상이면 통과
        is_resolution_ok = properties.get("width", 0) == 1080 and properties.get("height", 0) == 1920
        is_fps_ok = 29 <= properties.get("fps", 0) <= 31

        verification_result = {
            "path": str(video_path.relative_to(ROOT_DIR)),
            "properties": properties,
            "checks": {
                "bitrate_ok (>=7000k)": is_bitrate_ok,
                "resolution_ok (1080x1920)": is_resolution_ok,
                "fps_ok (30)": is_fps_ok
            },
            "overall_status": "PASS" if is_bitrate_ok and is_resolution_ok and is_fps_ok else "FAIL"
        }
        report["videos"].append(verification_result)
        logger.info(f"Verified {video_path.name}: {verification_result['overall_status']}")

    # 리포트 저장
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    logger.success(f"Quality verification complete. Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    from datetime import datetime
    verify_quality()