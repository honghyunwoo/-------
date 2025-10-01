"""
프리미엄 영상 소스 통합 서비스
Pexels, Pixabay, Unsplash 등 다중 소스 지원
"""
import os
import random
import requests
from typing import List, Dict, Optional
from loguru import logger

class VideoSourceManager:
    """영상 소스 통합 관리자"""

    def __init__(self):
        # API 키 설정
        self.pexels_keys = self._get_api_keys("PEXELS_API_KEYS", [
            "84S18I3DIXma1iV3xyT6uIQb9fxSzH6h77NhiLxNYZtTHRCu1Il6Auwb"
        ])
        self.pixabay_keys = self._get_api_keys("PIXABAY_API_KEYS", [
            "your-pixabay-key"
        ])
        self.unsplash_keys = self._get_api_keys("UNSPLASH_API_KEYS", [
            "your-unsplash-key"
        ])

        # 한국 콘텐츠 우선 키워드
        self.korean_keywords = {
            "음식": ["korean food", "kimchi", "bulgogi", "bibimbap", "korean cuisine"],
            "풍경": ["seoul", "busan", "jeju", "korean temple", "hanok village"],
            "문화": ["k-pop", "hanbok", "korean culture", "taekwondo", "korean art"],
            "비즈니스": ["seoul business", "gangnam", "korean office", "tech korea"],
            "교육": ["korean school", "study korea", "education asia"],
        }

    def _get_api_keys(self, env_name: str, defaults: List[str]) -> List[str]:
        """환경변수에서 API 키 가져오기"""
        keys_str = os.getenv(env_name, "")
        if keys_str:
            return keys_str.split(",")
        return defaults

    def search_videos(self, query: str, count: int = 10,
                     source: str = "mixed") -> List[Dict]:
        """
        영상 검색 (다중 소스 지원)

        Args:
            query: 검색 키워드
            count: 필요한 영상 개수
            source: 소스 타입 (pexels, pixabay, unsplash, mixed)

        Returns:
            영상 정보 리스트
        """
        videos = []

        # 한국 관련 키워드 강화
        enhanced_query = self._enhance_korean_query(query)

        if source == "mixed" or source == "pexels":
            videos.extend(self._search_pexels(enhanced_query, count))

        if source == "mixed" or source == "pixabay":
            videos.extend(self._search_pixabay(enhanced_query, count))

        if source == "mixed" or source == "unsplash":
            videos.extend(self._search_unsplash(enhanced_query, count))

        # 중복 제거 및 품질 정렬
        videos = self._filter_quality(videos)

        # 필요한 개수만큼 반환
        return videos[:count]

    def _enhance_korean_query(self, query: str) -> str:
        """한국 관련 키워드 강화"""
        # 한국어 키워드를 영어로 변환하고 관련 키워드 추가
        query_lower = query.lower()

        for category, keywords in self.korean_keywords.items():
            if any(word in query_lower for word in ["음식", "food", "맛집"]):
                return f"{query} {random.choice(self.korean_keywords['음식'])}"
            elif any(word in query_lower for word in ["풍경", "여행", "관광"]):
                return f"{query} {random.choice(self.korean_keywords['풍경'])}"
            elif any(word in query_lower for word in ["문화", "k-pop", "한국"]):
                return f"{query} {random.choice(self.korean_keywords['문화'])}"

        return query

    def _search_pexels(self, query: str, count: int) -> List[Dict]:
        """Pexels API 검색"""
        videos = []
        api_key = random.choice(self.pexels_keys)

        headers = {
            "Authorization": api_key
        }

        try:
            response = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={
                    "query": query,
                    "per_page": count,
                    "orientation": "portrait"  # 세로 영상 우선
                }
            )

            if response.status_code == 200:
                data = response.json()
                for video in data.get("videos", []):
                    # HD 품질 우선
                    video_files = video.get("video_files", [])
                    hd_files = [f for f in video_files if f.get("quality") == "hd"]

                    if hd_files:
                        videos.append({
                            "source": "pexels",
                            "url": hd_files[0]["link"],
                            "duration": video.get("duration", 0),
                            "width": hd_files[0].get("width", 1920),
                            "height": hd_files[0].get("height", 1080),
                            "quality": "hd",
                            "description": video.get("description", "")
                        })

        except Exception as e:
            logger.error(f"Pexels 검색 실패: {e}")

        return videos

    def _search_pixabay(self, query: str, count: int) -> List[Dict]:
        """Pixabay API 검색"""
        videos = []
        api_key = random.choice(self.pixabay_keys)

        try:
            response = requests.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": api_key,
                    "q": query,
                    "per_page": count,
                    "video_type": "film",
                    "min_width": 1920,
                    "min_height": 1080
                }
            )

            if response.status_code == 200:
                data = response.json()
                for video in data.get("hits", []):
                    videos.append({
                        "source": "pixabay",
                        "url": video.get("videos", {}).get("large", {}).get("url", ""),
                        "duration": video.get("duration", 0),
                        "width": video.get("videos", {}).get("large", {}).get("width", 1920),
                        "height": video.get("videos", {}).get("large", {}).get("height", 1080),
                        "quality": "hd",
                        "description": video.get("tags", "")
                    })

        except Exception as e:
            logger.error(f"Pixabay 검색 실패: {e}")

        return videos

    def _search_unsplash(self, query: str, count: int) -> List[Dict]:
        """Unsplash API 검색 (주로 이미지, 비디오는 제한적)"""
        # Unsplash는 주로 이미지 API이므로 비디오 대신 고품질 이미지 사용
        videos = []
        # 구현 생략 (Unsplash는 비디오 API가 제한적)
        return videos

    def _filter_quality(self, videos: List[Dict]) -> List[Dict]:
        """품질 기준으로 필터링 및 정렬"""
        # HD 품질 우선
        hd_videos = [v for v in videos if v.get("quality") == "hd"]

        # 중복 URL 제거
        seen_urls = set()
        unique_videos = []
        for video in hd_videos:
            if video["url"] not in seen_urls:
                seen_urls.add(video["url"])
                unique_videos.append(video)

        # 해상도 기준 정렬 (높은 해상도 우선)
        unique_videos.sort(
            key=lambda x: x.get("width", 0) * x.get("height", 0),
            reverse=True
        )

        return unique_videos

    def get_premium_sources(self) -> Dict[str, bool]:
        """프리미엄 소스 가용성 확인"""
        return {
            "pexels": len(self.pexels_keys) > 0,
            "pixabay": len(self.pixabay_keys) > 0 and self.pixabay_keys[0] != "your-pixabay-key",
            "unsplash": len(self.unsplash_keys) > 0 and self.unsplash_keys[0] != "your-unsplash-key",
        }

# 싱글톤 인스턴스
video_source_manager = VideoSourceManager()