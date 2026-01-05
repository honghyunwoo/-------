"""
BGM Downloader for Shorts Factory
Pixabay Music API를 사용해 무드별 BGM 다운로드

사용법:
    python scripts/download_bgm.py
    python scripts/download_bgm.py --mood calm
    python scripts/download_bgm.py --list
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_MUSIC_URL = "https://pixabay.com/api/music/"

# 출력 경로
OUTPUT_BASE = Path(__file__).parent.parent / "assets" / "bgm"

# 무드별 검색 키워드 및 설정
MOOD_CONFIGS = {
    "calm": {
        "keywords": ["meditation music", "calm ambient", "peaceful piano", "relaxing background"],
        "description": "차분하고 명상적인 분위기",
        "target_count": 4,
        "min_duration": 60,  # 최소 60초
        "max_duration": 300,  # 최대 5분
    },
    "inspiring": {
        "keywords": ["inspiring music", "motivational", "uplifting background", "hopeful piano"],
        "description": "희망적이고 동기부여 분위기",
        "target_count": 4,
        "min_duration": 60,
        "max_duration": 300,
    },
    "dramatic": {
        "keywords": ["epic cinematic", "dramatic orchestral", "powerful music", "intense background"],
        "description": "드라마틱하고 강렬한 분위기",
        "target_count": 3,
        "min_duration": 60,
        "max_duration": 300,
    },
    "reflective": {
        "keywords": ["melancholy piano", "sad ambient", "thoughtful music", "introspective"],
        "description": "성찰적이고 사색적인 분위기",
        "target_count": 3,
        "min_duration": 60,
        "max_duration": 300,
    },
}

# 다운로드된 트랙 추적
downloaded_tracks = {}


def load_downloaded_tracks():
    """이미 다운로드된 트랙 로드"""
    global downloaded_tracks
    tracking_file = OUTPUT_BASE / "downloaded_tracks.json"
    if tracking_file.exists():
        with open(tracking_file, 'r', encoding='utf-8') as f:
            downloaded_tracks = json.load(f)
    return downloaded_tracks


def save_downloaded_tracks():
    """다운로드된 트랙 저장"""
    tracking_file = OUTPUT_BASE / "downloaded_tracks.json"
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(downloaded_tracks, f, ensure_ascii=False, indent=2)


def search_pixabay_music(query: str, per_page: int = 20) -> list:
    """Pixabay Music API로 검색"""
    if not PIXABAY_API_KEY:
        print("[ERROR] PIXABAY_API_KEY not configured!")
        print("Get free API key from: https://pixabay.com/api/docs/")
        return []

    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": per_page,
    }

    try:
        response = requests.get(PIXABAY_MUSIC_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("hits", [])
    except requests.RequestException as e:
        print(f"[ERROR] Search failed: {e}")
        return []


def download_track(track: dict, mood: str) -> bool:
    """트랙 다운로드"""
    track_id = str(track.get("id"))

    if track_id in downloaded_tracks:
        return False  # 이미 다운로드됨

    audio_url = track.get("audio")
    if not audio_url:
        return False

    # 출력 폴더
    output_dir = OUTPUT_BASE / mood
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파일명 생성 (안전한 이름)
    title = track.get("title", "untitled").replace(" ", "_")[:30]
    filename = f"{mood}_{track_id}_{title}.mp3"
    output_path = output_dir / filename

    if output_path.exists():
        downloaded_tracks[track_id] = {
            "mood": mood,
            "title": track.get("title"),
            "duration": track.get("duration"),
            "path": str(output_path)
        }
        return False

    try:
        response = requests.get(audio_url, stream=True, timeout=120)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        downloaded_tracks[track_id] = {
            "mood": mood,
            "title": track.get("title"),
            "duration": track.get("duration"),
            "path": str(output_path),
            "downloaded_at": datetime.now().isoformat()
        }
        return True

    except Exception as e:
        print(f"[ERROR] Download failed {track_id}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_mood(mood: str) -> int:
    """무드별 BGM 다운로드"""
    config = MOOD_CONFIGS.get(mood)
    if not config:
        print(f"[ERROR] Unknown mood: {mood}")
        return 0

    # 이미 다운로드된 개수 확인
    existing = sum(1 for t in downloaded_tracks.values() if t.get("mood") == mood)
    needed = config["target_count"] - existing

    if needed <= 0:
        print(f"[SKIP] {mood}: already has {existing} tracks")
        return 0

    print(f"\n{'='*50}")
    print(f"[MOOD] {mood}")
    print(f"[DESC] {config['description']}")
    print(f"[TARGET] {config['target_count']} tracks (need {needed} more)")
    print(f"{'='*50}")

    downloaded = 0

    for keyword in config["keywords"]:
        if downloaded >= needed:
            break

        print(f"\n  Searching: '{keyword}'...")
        tracks = search_pixabay_music(keyword)

        if not tracks:
            continue

        for track in tracks:
            if downloaded >= needed:
                break

            # 길이 필터링
            duration = track.get("duration", 0)
            if duration < config["min_duration"] or duration > config["max_duration"]:
                continue

            if download_track(track, mood):
                downloaded += 1
                print(f"    [{downloaded}/{needed}] Downloaded: {track.get('title', 'Unknown')}")

    print(f"\n[DONE] {mood}: Downloaded {downloaded} new tracks")
    return downloaded


def get_mood_summary() -> dict:
    """무드별 현황 요약"""
    summary = {}
    for mood in MOOD_CONFIGS.keys():
        count = sum(1 for t in downloaded_tracks.values() if t.get("mood") == mood)
        target = MOOD_CONFIGS[mood]["target_count"]
        summary[mood] = {"current": count, "target": target}
    return summary


def main():
    parser = argparse.ArgumentParser(description="BGM Downloader for Shorts Factory")
    parser.add_argument("--mood", type=str, default="all", help="Mood to download (or 'all')")
    parser.add_argument("--list", action="store_true", help="List all moods and current status")

    args = parser.parse_args()

    # 기존 트랙 로드
    load_downloaded_tracks()

    if args.list:
        print("\n=== BGM Library Status ===")
        summary = get_mood_summary()
        for mood, status in summary.items():
            config = MOOD_CONFIGS[mood]
            print(f"  {mood}: {status['current']}/{status['target']} - {config['description']}")
        print(f"\nTotal: {len(downloaded_tracks)} tracks")
        return

    # API 키 확인
    if not PIXABAY_API_KEY:
        print("[INFO] PIXABAY_API_KEY not found.")
        print("[INFO] BGM can be downloaded manually from pixabay.com/music/")
        print("[INFO] Place files in: assets/bgm/<mood>/")
        print("\nAlternative: Get free API key from https://pixabay.com/api/docs/")
        return

    print(f"\n{'='*60}")
    print(f"  BGM Downloader for Shorts Factory")
    print(f"  Moods: {len(MOOD_CONFIGS)}")
    print(f"  Total target: {sum(c['target_count'] for c in MOOD_CONFIGS.values())} tracks")
    print(f"{'='*60}")

    # 다운로드 시작
    start_time = datetime.now()
    total_downloaded = 0

    moods_to_process = [args.mood] if args.mood != "all" else list(MOOD_CONFIGS.keys())

    for mood in moods_to_process:
        if mood not in MOOD_CONFIGS:
            print(f"[ERROR] Unknown mood: {mood}")
            continue

        count = download_mood(mood)
        total_downloaded += count
        save_downloaded_tracks()

    # 완료 보고
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    print(f"  COMPLETED!")
    print(f"  Downloaded: {total_downloaded} new tracks")
    print(f"  Time: {elapsed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
