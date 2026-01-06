"""
B-roll 선택 모듈
테마 기반 배경 영상 선택 + 인덱스 캐싱
"""

import json
import logging
import random
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BrollClip:
    """B-roll 클립 정보"""
    path: Path
    duration: float  # 초 단위
    themes: List[str] = field(default_factory=list)
    source: str = ""  # 출처 (예: pexels, pixabay)
    resolution: str = ""  # 예: 1080x1920

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "duration": self.duration,
            "themes": self.themes,
            "source": self.source,
            "resolution": self.resolution
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BrollClip':
        return cls(
            path=Path(data["path"]),
            duration=data.get("duration", 10.0),
            themes=data.get("themes", []),
            source=data.get("source", ""),
            resolution=data.get("resolution", "")
        )


@dataclass
class BrollConfig:
    """B-roll 설정"""
    assets_path: Path
    index_file: str = "broll_index.json"
    supported_formats: tuple = (".mp4", ".mov", ".webm")
    default_duration: float = 10.0  # 클립 기본 길이 추정값


class BrollSelector:
    """B-roll 선택기"""

    # 비디오 길이 캐시 (파일 경로 → 길이)
    _duration_cache: Dict[str, float] = {}

    # 테마별 키워드 매핑
    THEME_KEYWORDS = {
        "역경": ["mountain", "storm", "rain", "struggle", "climbing"],
        "마음": ["meditation", "peace", "calm", "nature", "water"],
        "시간": ["clock", "hourglass", "sunset", "sunrise", "time-lapse"],
        "통제": ["control", "focus", "discipline", "routine"],
        "죽음": ["autumn", "leaves", "cycle", "ending", "memorial"],
        "미덕": ["light", "growth", "garden", "wisdom"],
        "행복": ["joy", "smile", "celebration", "sunshine"],
        "자연": ["nature", "forest", "ocean", "sky", "landscape"],
        "도시": ["city", "urban", "building", "street"],
        "추상": ["abstract", "particles", "geometric", "motion"]
    }

    def __init__(self, config: BrollConfig = None, assets_path: Path = None, fast_scan: bool = True):
        if config:
            self.config = config
        else:
            self.config = BrollConfig(
                assets_path=assets_path or Path("./assets/b-roll")
            )
        self.clips: List[BrollClip] = []
        self.fast_scan = fast_scan  # True면 duration 체크 건너뛰기
        self._load_index()

    def _load_index(self):
        """인덱스 파일에서 클립 정보 로드 (캐시 검증 포함)"""
        index_path = self.config.assets_path / self.config.index_file

        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 캐시 유효성 검증
                if self._is_cache_valid(data):
                    self.clips = [BrollClip.from_dict(c) for c in data.get("clips", [])]
                    logger.info(f"[Cache] Loaded {len(self.clips)} clips from index (0.01s)")
                    return
                else:
                    logger.info("[Cache] Index expired, rescanning...")

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"[Cache] Index corrupted: {e}")

        # 인덱스가 없거나 만료되면 폴더 스캔
        self.clips = self._scan_folder()
        if self.clips:
            self.save_index()
            logger.info(f"[Cache] Created new index with {len(self.clips)} clips")

    def _is_cache_valid(self, data: dict) -> bool:
        """캐시 유효성 검사 (폴더 수정 시간 비교)"""
        cache_time = data.get("last_updated")
        if not cache_time:
            return False

        try:
            cache_dt = datetime.fromisoformat(cache_time)

            # 폴더의 가장 최근 수정 시간 확인
            folder_mtime = self._get_folder_mtime()
            if folder_mtime and folder_mtime > cache_dt:
                return False

            # 클립 수 검증 (빠른 체크)
            expected_count = data.get("total_count", 0)
            actual_count = self._count_video_files()
            if abs(expected_count - actual_count) > 2:  # 오차 허용
                return False

            return True

        except (ValueError, OSError):
            return False

    def _get_folder_mtime(self) -> Optional[datetime]:
        """폴더의 최신 수정 시간 반환"""
        if not self.config.assets_path.exists():
            return None

        latest = None
        for ext in self.config.supported_formats:
            for video_file in self.config.assets_path.rglob(f"*{ext}"):
                mtime = datetime.fromtimestamp(video_file.stat().st_mtime)
                if latest is None or mtime > latest:
                    latest = mtime
                break  # 첫 파일만 체크 (빠른 검증)

        return latest

    def _count_video_files(self) -> int:
        """비디오 파일 수 빠르게 카운트"""
        if not self.config.assets_path.exists():
            return 0

        count = 0
        for ext in self.config.supported_formats:
            count += len(list(self.config.assets_path.rglob(f"*{ext}")))
        return count

    def _scan_folder(self) -> List[BrollClip]:
        """B-roll 폴더 스캔 (fast_scan=True면 duration 체크 건너뜀)"""
        clips = []

        if not self.config.assets_path.exists():
            return clips

        for ext in self.config.supported_formats:
            for video_file in self.config.assets_path.rglob(f"*{ext}"):
                # 폴더 이름에서 테마 추출
                themes = self._extract_themes_from_path(video_file)

                # fast_scan이면 기본 duration 사용 (빠름)
                if self.fast_scan:
                    duration = self.config.default_duration
                else:
                    duration = self._get_video_duration(video_file)

                clip = BrollClip(
                    path=video_file,
                    duration=duration,
                    themes=themes,
                    source="local"
                )
                clips.append(clip)

        return clips

    def _extract_themes_from_path(self, path: Path) -> List[str]:
        """파일 경로에서 테마 추출"""
        themes = []
        path_str = str(path).lower()

        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in path_str for kw in keywords + [theme.lower()]):
                themes.append(theme)

        # 폴더 이름도 테마로 추가
        parent_name = path.parent.name.lower()
        if parent_name and parent_name not in ["b-roll", "broll"]:
            themes.append(parent_name)

        return list(set(themes)) or ["general"]

    def _get_video_duration(self, path: Path) -> float:
        """비디오 길이 반환 (캐시 사용)"""
        path_str = str(path)

        # 캐시 확인
        if path_str in self._duration_cache:
            return self._duration_cache[path_str]

        try:
            from moviepy import VideoFileClip
            with VideoFileClip(str(path)) as clip:
                duration = clip.duration
                self._duration_cache[path_str] = duration
                return duration
        except Exception as e:
            logger.warning(f"비디오 길이 측정 실패 ({path.name}): {e}, 기본값 사용")
            return self.config.default_duration

    def select(
        self,
        themes: List[str],
        target_duration: float,
        avoid_repeats: bool = True
    ) -> List[BrollClip]:
        """테마에 맞는 클립 선택"""
        if not self.clips:
            return []

        # 1. 테마 매칭 클립 필터링
        matching = self._filter_by_themes(themes)

        if not matching:
            # 매칭되는 클립이 없으면 전체에서 선택
            matching = self.clips.copy()

        # 2. 필요 길이에 맞게 클립 선택
        selected = []
        total_duration = 0.0
        used_paths = set()

        while total_duration < target_duration and matching:
            # 랜덤 선택
            available = [c for c in matching if str(c.path) not in used_paths] if avoid_repeats else matching

            if not available:
                # 반복 허용으로 전환
                available = matching

            clip = random.choice(available)
            selected.append(clip)
            total_duration += clip.duration

            if avoid_repeats:
                used_paths.add(str(clip.path))

        return selected

    def _filter_by_themes(self, themes: List[str]) -> List[BrollClip]:
        """테마로 클립 필터링"""
        if not themes:
            return self.clips.copy()

        matching = []
        themes_lower = [t.lower() for t in themes]

        for clip in self.clips:
            clip_themes_lower = [t.lower() for t in clip.themes]
            if any(t in clip_themes_lower for t in themes_lower):
                matching.append(clip)

        return matching

    def select_by_category(
        self,
        category: str,
        target_duration: float
    ) -> List[BrollClip]:
        """카테고리로 클립 선택"""
        category_path = self.config.assets_path / category

        if not category_path.exists():
            return self.select([], target_duration)

        category_clips = [c for c in self.clips if category_path in c.path.parents]

        if not category_clips:
            return self.select([], target_duration)

        selected = []
        total = 0.0

        while total < target_duration and category_clips:
            clip = random.choice(category_clips)
            selected.append(clip)
            total += clip.duration

        return selected

    def save_index(self):
        """인덱스 파일 저장 (타임스탬프 포함)"""
        index_path = self.config.assets_path / self.config.index_file
        index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "last_updated": datetime.now().isoformat(),
            "total_count": len(self.clips),
            "total_duration": sum(c.duration for c in self.clips),
            "themes": list(set(t for c in self.clips for t in c.themes)),
            "clips": [c.to_dict() for c in self.clips]
        }

        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[Cache] Saved index: {len(self.clips)} clips")

    def refresh_index(self):
        """인덱스 새로고침 (폴더 재스캔)"""
        self.clips = self._scan_folder()
        self.save_index()

    def add_clip(self, clip: BrollClip):
        """클립 추가"""
        self.clips.append(clip)

    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        total_duration = sum(c.duration for c in self.clips)
        themes = {}
        for clip in self.clips:
            for theme in clip.themes:
                themes[theme] = themes.get(theme, 0) + 1

        return {
            "total_clips": len(self.clips),
            "total_duration": total_duration,
            "themes": themes,
            "avg_duration": total_duration / len(self.clips) if self.clips else 0
        }


class BrollDownloader:
    """B-roll 다운로드 유틸리티 (Pexels, Pixabay)"""

    PEXELS_API = "https://api.pexels.com/videos/search"
    PIXABAY_API = "https://pixabay.com/api/videos/"

    def __init__(self, output_path: Path, pexels_key: str = None, pixabay_key: str = None):
        self.output_path = Path(output_path)
        self.pexels_key = pexels_key
        self.pixabay_key = pixabay_key

    def search_pexels(self, query: str, per_page: int = 5) -> List[dict]:
        """Pexels에서 비디오 검색"""
        if not self.pexels_key:
            return []

        import requests

        headers = {"Authorization": self.pexels_key}
        params = {"query": query, "per_page": per_page, "orientation": "portrait"}

        try:
            response = requests.get(self.PEXELS_API, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("videos", [])
        except Exception:
            return []

    def download_video(self, url: str, filename: str, category: str = "general") -> Optional[Path]:
        """비디오 다운로드"""
        import requests

        output_dir = self.output_path / category
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_file
        except Exception:
            return None
