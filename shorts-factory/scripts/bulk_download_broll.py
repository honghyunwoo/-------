"""
B-roll Bulk Downloader
Pexels API를 사용해 카테고리별 100개씩 다운로드

사용법:
    python scripts/bulk_download_broll.py
    python scripts/bulk_download_broll.py --category nature_epic
    python scripts/bulk_download_broll.py --category all --per-category 100
"""

import os
import sys
import time
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_API_URL = "https://api.pexels.com/videos/search"

# 출력 경로
OUTPUT_BASE = Path(__file__).parent.parent / "assets" / "b-roll"

# 카테고리별 검색 키워드 (영어)
CATEGORIES = {
    # 기존 카테고리 (확장)
    "stoic": ["stoic philosophy", "ancient greece", "roman empire", "philosopher thinking"],
    "stoic_statue": ["greek statue", "roman sculpture", "marble bust", "ancient statue"],
    "meditation": ["meditation", "mindfulness", "zen garden", "peaceful yoga", "breathing exercise"],
    "nature_epic": ["epic nature", "mountain peak", "vast landscape", "drone nature", "majestic scenery"],
    "storm_adversity": ["storm clouds", "thunderstorm", "lightning", "dramatic weather", "rain storm"],
    "sunrise_hope": ["sunrise timelapse", "golden hour", "dawn sky", "morning light", "new day"],
    "sunset_reflection": ["sunset ocean", "sunset silhouette", "evening sky", "dusk clouds", "twilight"],
    "time_passing": ["clock timelapse", "hourglass sand", "time lapse clouds", "seasons changing", "aging"],
    "fire_focus": ["candle flame", "fireplace", "campfire", "bonfire night", "fire closeup"],
    "water_flow": ["waterfall", "river flow", "ocean waves", "rain drops", "water stream"],
    "dark_cinematic": ["dark abstract", "smoke black background", "particles dark", "cinematic dark", "noir"],
    "fog_mystery": ["fog forest", "misty morning", "mysterious fog", "haze landscape", "foggy road"],
    "stars_universe": ["stars night sky", "galaxy space", "universe cosmos", "milky way", "starry night"],
    "walking_journey": ["walking path", "hiking trail", "journey road", "footsteps", "adventure walk"],
    "writing_wisdom": ["writing journal", "old books", "library study", "pen paper", "wisdom scroll"],
    "abstract": ["abstract motion", "geometric shapes", "particles flow", "light rays", "fluid motion"],
    "city": ["city skyline", "urban night", "city traffic", "building architecture", "city timelapse"],

    # 새 카테고리 (자기개발 확장)
    "success_business": ["business success", "office working", "entrepreneur", "corporate meeting", "achievement"],
    "growth_plants": ["plant growing timelapse", "seeds sprouting", "tree growth", "nature growth", "flourishing"],
    "books_learning": ["books library", "reading book", "studying", "knowledge education", "open book pages"],
    "fitness_health": ["fitness workout", "running exercise", "gym training", "healthy lifestyle", "yoga stretching"],
    "mindset_brain": ["brain thinking", "focus concentration", "mental clarity", "neuroscience", "mind power"],
    "relationship": ["people connection", "handshake deal", "teamwork collaboration", "friendship", "community"],
    "money_wealth": ["money coins", "investment growth", "financial success", "gold wealth", "prosperity"],
    "technology": ["technology laptop", "coding programming", "digital innovation", "futuristic tech", "computer work"],
}

# 이미 다운로드된 비디오 ID 추적
downloaded_ids = set()


def load_downloaded_ids():
    """이미 다운로드된 ID 로드"""
    global downloaded_ids
    tracking_file = OUTPUT_BASE / "downloaded_ids.json"
    if tracking_file.exists():
        with open(tracking_file, 'r') as f:
            downloaded_ids = set(json.load(f))
    return downloaded_ids


def save_downloaded_ids():
    """다운로드된 ID 저장"""
    tracking_file = OUTPUT_BASE / "downloaded_ids.json"
    with open(tracking_file, 'w') as f:
        json.dump(list(downloaded_ids), f)


def search_pexels(query: str, per_page: int = 80, page: int = 1, orientation: str = "portrait") -> list:
    """Pexels API로 비디오 검색"""
    if not PEXELS_API_KEY:
        print("[ERROR] PEXELS_API_KEY not configured!")
        return []

    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": min(per_page, 80),  # Pexels 최대 80
        "page": page,
        "orientation": orientation,
    }

    try:
        response = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("videos", [])
    except requests.RequestException as e:
        print(f"[ERROR] Search failed: {e}")
        return []


def get_best_video_file(video: dict, max_height: int = 1920) -> dict:
    """최적의 비디오 파일 선택 (세로 우선)"""
    video_files = video.get("video_files", [])

    # 세로 형식 우선, 해상도 1080p 이하
    suitable = []
    for vf in video_files:
        height = vf.get("height", 0)
        width = vf.get("width", 0)

        # 세로 형식 (height > width) 또는 적당한 해상도
        if height <= max_height and vf.get("link"):
            suitable.append(vf)

    if not suitable:
        return video_files[0] if video_files else None

    # 해상도 높은 순 정렬
    suitable.sort(key=lambda x: x.get("height", 0), reverse=True)
    return suitable[0]


def download_video(video: dict, category: str) -> bool:
    """비디오 다운로드"""
    video_id = video.get("id")

    if video_id in downloaded_ids:
        return False  # 이미 다운로드됨

    video_file = get_best_video_file(video)
    if not video_file:
        return False

    url = video_file.get("link")
    if not url:
        return False

    # 출력 폴더
    output_dir = OUTPUT_BASE / category
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파일명 생성
    filename = f"{category}_{video_id}.mp4"
    output_path = output_dir / filename

    if output_path.exists():
        downloaded_ids.add(video_id)
        return False  # 이미 존재

    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        downloaded_ids.add(video_id)
        return True

    except Exception as e:
        print(f"[ERROR] Download failed {video_id}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_category(category: str, target_count: int = 100, existing_count: int = 0) -> int:
    """카테고리별 다운로드"""
    keywords = CATEGORIES.get(category, [category])
    needed = target_count - existing_count

    if needed <= 0:
        print(f"[SKIP] {category}: already has {existing_count} clips")
        return 0

    print(f"\n{'='*50}")
    print(f"[CATEGORY] {category}")
    print(f"[TARGET] {target_count} clips (need {needed} more)")
    print(f"[KEYWORDS] {', '.join(keywords)}")
    print(f"{'='*50}")

    downloaded = 0

    for keyword in keywords:
        if downloaded >= needed:
            break

        print(f"\n  Searching: '{keyword}'...")

        # 여러 페이지 검색
        for page in range(1, 4):  # 최대 3페이지
            if downloaded >= needed:
                break

            videos = search_pexels(keyword, per_page=80, page=page)

            if not videos:
                break

            for video in videos:
                if downloaded >= needed:
                    break

                if download_video(video, category):
                    downloaded += 1
                    print(f"    [{downloaded}/{needed}] Downloaded: {video.get('id')}")

            # API 레이트 리밋 방지
            time.sleep(1)

    print(f"\n[DONE] {category}: Downloaded {downloaded} new clips")
    return downloaded


def get_existing_counts() -> dict:
    """기존 클립 수 확인"""
    counts = {}
    for category in CATEGORIES.keys():
        category_path = OUTPUT_BASE / category
        if category_path.exists():
            counts[category] = len(list(category_path.glob("*.mp4")))
        else:
            counts[category] = 0
    return counts


def main():
    parser = argparse.ArgumentParser(description="B-roll Bulk Downloader")
    parser.add_argument("--category", type=str, default="all", help="Category to download (or 'all')")
    parser.add_argument("--per-category", type=int, default=100, help="Target clips per category")
    parser.add_argument("--list", action="store_true", help="List all categories")

    args = parser.parse_args()

    if args.list:
        print("\n=== Available Categories ===")
        for cat, keywords in CATEGORIES.items():
            print(f"  {cat}: {', '.join(keywords[:2])}...")
        print(f"\nTotal: {len(CATEGORIES)} categories")
        return

    # API 키 확인
    if not PEXELS_API_KEY:
        print("[ERROR] PEXELS_API_KEY not found in config/.env")
        return

    print(f"\n{'='*60}")
    print(f"  B-roll Bulk Downloader")
    print(f"  Target: {args.per_category} clips per category")
    print(f"  Categories: {len(CATEGORIES)}")
    print(f"  Total target: {args.per_category * len(CATEGORIES)} clips")
    print(f"{'='*60}")

    # 기존 클립 수 확인
    existing = get_existing_counts()
    load_downloaded_ids()

    # 다운로드 시작
    start_time = datetime.now()
    total_downloaded = 0

    categories_to_process = [args.category] if args.category != "all" else list(CATEGORIES.keys())

    for category in categories_to_process:
        if category not in CATEGORIES:
            print(f"[ERROR] Unknown category: {category}")
            continue

        count = download_category(
            category,
            target_count=args.per_category,
            existing_count=existing.get(category, 0)
        )
        total_downloaded += count

        # 진행 상황 저장
        save_downloaded_ids()

    # 완료 보고
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    print(f"  COMPLETED!")
    print(f"  Downloaded: {total_downloaded} new clips")
    print(f"  Time: {elapsed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
