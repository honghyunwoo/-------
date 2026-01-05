"""
Pexels B-roll 대량 다운로드 스크립트
카테고리별로 정리하여 다운로드
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# .env 로드
load_dotenv(PROJECT_ROOT / "config" / ".env")


@dataclass
class DownloadConfig:
    """다운로드 설정"""
    output_dir: Path = PROJECT_ROOT / "assets" / "b-roll"
    pexels_key: str = os.getenv("PEXELS_API_KEY", "")
    per_category: int = 10  # 카테고리당 다운로드 개수
    orientation: str = "portrait"  # Shorts용 세로 영상
    min_duration: int = 5
    max_duration: int = 60
    resolution: str = "hd"  # sd, hd, uhd


# 스토아 철학 + 성공 채널 분석 기반 카테고리
CATEGORIES = {
    # 핵심 스토아 테마
    "stoic_statue": {
        "queries": ["greek statue", "roman sculpture", "marble bust", "ancient statue"],
        "themes": ["스토아", "철학", "고대", "조각상"]
    },
    "meditation": {
        "queries": ["meditation", "zen", "peaceful nature", "calm water reflection"],
        "themes": ["마음", "명상", "평화", "고요"]
    },
    "nature_epic": {
        "queries": ["epic nature", "mountain peak", "vast ocean", "dramatic landscape"],
        "themes": ["자연", "장엄", "웅장"]
    },

    # 감정/상태
    "storm_adversity": {
        "queries": ["storm clouds", "thunderstorm", "rain storm", "dramatic weather"],
        "themes": ["역경", "시련", "폭풍"]
    },
    "sunrise_hope": {
        "queries": ["sunrise timelapse", "golden hour", "dawn sky", "morning light"],
        "themes": ["희망", "시작", "새벽"]
    },
    "sunset_reflection": {
        "queries": ["sunset ocean", "sunset silhouette", "evening sky", "dusk"],
        "themes": ["마무리", "성찰", "저녁"]
    },

    # 시간/흐름
    "time_passing": {
        "queries": ["clock timelapse", "hourglass", "time lapse clouds", "seasons change"],
        "themes": ["시간", "흐름", "변화"]
    },
    "fire_focus": {
        "queries": ["candle flame", "fireplace", "campfire", "bonfire night"],
        "themes": ["집중", "열정", "불"]
    },
    "water_flow": {
        "queries": ["waterfall", "river flow", "ocean waves", "rain drops"],
        "themes": ["흐름", "물", "자연"]
    },

    # 추상/배경
    "dark_cinematic": {
        "queries": ["dark abstract", "smoke black", "particles dark", "cinematic dark"],
        "themes": ["추상", "시네마틱", "어둠"]
    },
    "fog_mystery": {
        "queries": ["fog forest", "misty morning", "foggy landscape", "mysterious fog"],
        "themes": ["안개", "신비", "숲"]
    },
    "stars_universe": {
        "queries": ["stars night sky", "milky way", "universe", "galaxy timelapse"],
        "themes": ["우주", "별", "밤하늘"]
    },

    # 인간/활동
    "walking_journey": {
        "queries": ["person walking", "hiking trail", "journey path", "walking alone"],
        "themes": ["여정", "걷기", "길"]
    },
    "writing_wisdom": {
        "queries": ["writing journal", "pen paper", "old book pages", "reading book"],
        "themes": ["지혜", "글쓰기", "책"]
    }
}


class PexelsDownloader:
    """Pexels API 다운로더"""

    BASE_URL = "https://api.pexels.com/videos/search"

    def __init__(self, config: DownloadConfig):
        self.config = config
        self.headers = {"Authorization": config.pexels_key}
        self.downloaded = []
        self.errors = []

    def search_videos(self, query: str, per_page: int = 10) -> List[Dict]:
        """비디오 검색"""
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": self.config.orientation,
            "size": "medium"  # small, medium, large
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("videos", [])
        except Exception as e:
            print(f"  [!] 검색 실패: {query} - {e}")
            return []

    def get_best_file(self, video: Dict) -> Optional[Dict]:
        """최적 해상도 파일 선택 (세로 영상 우선)"""
        files = video.get("video_files", [])
        if not files:
            return None

        # 해상도별 정렬 (HD 우선)
        resolution_priority = {
            "hd": 3,
            "sd": 2,
            "uhd": 1  # UHD는 파일이 너무 큼
        }

        # 세로 영상 필터링 (height > width)
        portrait_files = [f for f in files if f.get("height", 0) > f.get("width", 0)]

        if portrait_files:
            files = portrait_files

        # 해상도 우선순위로 정렬
        sorted_files = sorted(
            files,
            key=lambda x: (
                resolution_priority.get(x.get("quality", ""), 0),
                x.get("height", 0)
            ),
            reverse=True
        )

        return sorted_files[0] if sorted_files else None

    def download_video(
        self,
        url: str,
        output_path: Path,
        video_id: int
    ) -> Optional[Path]:
        """비디오 다운로드"""
        try:
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_path
        except Exception as e:
            print(f"  [!] 다운로드 실패: {video_id} - {e}")
            return None

    def download_category(
        self,
        category: str,
        category_config: Dict,
        max_per_query: int = 3
    ) -> List[Dict]:
        """카테고리별 다운로드"""
        results = []
        output_dir = self.config.output_dir / category
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*50}")
        print(f"카테고리: {category}")
        print(f"테마: {', '.join(category_config['themes'])}")
        print(f"{'='*50}")

        existing_ids = set()
        for f in output_dir.glob("*.mp4"):
            # 파일명에서 ID 추출 (예: greek_statue_6875443.mp4)
            parts = f.stem.split("_")
            if parts:
                try:
                    existing_ids.add(int(parts[-1]))
                except ValueError:
                    pass

        for query in category_config["queries"]:
            print(f"\n  검색: '{query}'")
            videos = self.search_videos(query, per_page=max_per_query + 2)

            downloaded_count = 0
            for video in videos:
                if downloaded_count >= max_per_query:
                    break

                video_id = video.get("id")
                if video_id in existing_ids:
                    print(f"  [S] 이미 존재: {video_id}")
                    continue

                # 영상 길이 체크
                duration = video.get("duration", 0)
                if duration < self.config.min_duration or duration > self.config.max_duration:
                    continue

                best_file = self.get_best_file(video)
                if not best_file:
                    continue

                # 파일명 생성
                safe_query = query.replace(" ", "_").replace("/", "_")[:20]
                filename = f"{safe_query}_{video_id}.mp4"
                output_path = output_dir / filename

                print(f"  [D] 다운로드 중: {filename} ({duration}초)")

                result = self.download_video(
                    best_file["link"],
                    output_path,
                    video_id
                )

                if result:
                    results.append({
                        "path": str(output_path),
                        "duration": duration,
                        "themes": category_config["themes"],
                        "source": "pexels",
                        "video_id": video_id,
                        "resolution": f"{best_file.get('width', 0)}x{best_file.get('height', 0)}"
                    })
                    downloaded_count += 1
                    existing_ids.add(video_id)

                # API 레이트 리밋 방지
                time.sleep(0.5)

        print(f"\n  완료: {len(results)}개 다운로드")
        return results

    def download_all(self, categories: Dict = None, per_query: int = 3) -> Dict:
        """전체 카테고리 다운로드"""
        categories = categories or CATEGORIES
        all_results = {}
        total_downloaded = 0

        print("\n" + "="*60)
        print("Pexels B-roll 대량 다운로드 시작")
        print(f"카테고리: {len(categories)}개")
        print(f"쿼리당 다운로드: {per_query}개")
        print("="*60)

        for category, config in categories.items():
            results = self.download_category(category, config, per_query)
            all_results[category] = results
            total_downloaded += len(results)

            # 카테고리 간 대기
            time.sleep(1)

        print("\n" + "="*60)
        print(f"전체 완료: {total_downloaded}개 다운로드")
        print("="*60)

        return all_results

    def update_index(self, results: Dict):
        """broll_index.json 업데이트"""
        index_path = self.config.output_dir / "broll_index.json"

        # 기존 인덱스 로드
        existing_clips = []
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_clips = data.get("clips", [])
            except Exception:
                pass

        # 기존 경로 세트
        existing_paths = {c["path"] for c in existing_clips}

        # 새 클립 추가
        for category, clips in results.items():
            for clip in clips:
                if clip["path"] not in existing_paths:
                    existing_clips.append({
                        "path": clip["path"],
                        "duration": clip["duration"],
                        "themes": clip["themes"],
                        "source": clip["source"],
                        "resolution": clip.get("resolution", "")
                    })

        # 모든 테마 수집
        all_themes = list(set(
            theme
            for clip in existing_clips
            for theme in clip.get("themes", [])
        ))

        # 인덱스 저장
        index_data = {
            "clips": existing_clips,
            "total_count": len(existing_clips),
            "themes": all_themes,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"\n인덱스 업데이트 완료: {len(existing_clips)}개 클립")
        return index_data


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="Pexels B-roll 다운로드")
    parser.add_argument("--per-query", type=int, default=3, help="쿼리당 다운로드 개수")
    parser.add_argument("--category", type=str, help="특정 카테고리만 다운로드")
    parser.add_argument("--list", action="store_true", help="카테고리 목록 표시")
    args = parser.parse_args()

    if args.list:
        print("\n사용 가능한 카테고리:")
        for cat, config in CATEGORIES.items():
            print(f"  - {cat}: {', '.join(config['themes'])}")
        return

    config = DownloadConfig()

    if not config.pexels_key:
        print("오류: PEXELS_API_KEY가 설정되지 않았습니다.")
        print("config/.env 파일에 PEXELS_API_KEY를 설정하세요.")
        return

    downloader = PexelsDownloader(config)

    # 특정 카테고리 또는 전체
    if args.category:
        if args.category not in CATEGORIES:
            print(f"오류: 알 수 없는 카테고리 '{args.category}'")
            print("--list 옵션으로 카테고리 목록 확인")
            return
        categories = {args.category: CATEGORIES[args.category]}
    else:
        categories = CATEGORIES

    results = downloader.download_all(categories, per_query=args.per_query)
    downloader.update_index(results)

    # 통계 출력
    print("\n" + "="*60)
    print("카테고리별 통계:")
    for cat, clips in results.items():
        if clips:
            total_duration = sum(c["duration"] for c in clips)
            print(f"  {cat}: {len(clips)}개 ({total_duration:.0f}초)")
    print("="*60)


if __name__ == "__main__":
    main()
