#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
유튜브 트렌드 분석 모듈

이 모듈은 유튜브의 인기 동영상을 분석하여:
1. 현재 트렌딩 중인 주제 파악
2. 바이럴 키워드 추출
3. 최적의 영상 길이 분석
4. 인기 있는 콘텐츠 스타일 파악
"""

import re
import json
import requests
from typing import List, Dict, Optional, Tuple
from collections import Counter
from datetime import datetime, timedelta
from loguru import logger

from app.config import config


class YouTubeTrendAnalyzer:
    """유튜브 트렌드 분석기"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: 유튜브 Data API v3 키
        """
        self.api_key = api_key or config.app.get("youtube_api_key", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"

        if not self.api_key:
            logger.warning("YouTube API key not configured. Trend analysis will use fallback methods.")

    def get_trending_videos(
        self,
        region_code: str = "KR",
        category_id: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        인기 급상승 동영상 목록 가져오기

        Args:
            region_code: 국가 코드 (기본값: KR - 한국)
            category_id: 카테고리 ID (선택사항)
            max_results: 최대 결과 수 (1-50)

        Returns:
            인기 동영상 정보 리스트
        """
        if not self.api_key:
            logger.error("YouTube API key is required")
            return []

        try:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }

            if category_id:
                params["videoCategoryId"] = category_id

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            videos = []

            for item in data.get("items", []):
                video_info = {
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "view_count": int(item["statistics"].get("viewCount", 0)),
                    "like_count": int(item["statistics"].get("likeCount", 0)),
                    "comment_count": int(item["statistics"].get("commentCount", 0)),
                    "duration": item["contentDetails"]["duration"],
                    "tags": item["snippet"].get("tags", [])
                }
                videos.append(video_info)

            logger.info(f"Retrieved {len(videos)} trending videos from {region_code}")
            return videos

        except Exception as e:
            logger.error(f"Failed to get trending videos: {str(e)}")
            return []

    def extract_viral_keywords(
        self,
        videos: List[Dict],
        top_n: int = 20
    ) -> List[Tuple[str, int]]:
        """
        바이럴 키워드 추출

        Args:
            videos: 동영상 정보 리스트
            top_n: 상위 키워드 수

        Returns:
            (키워드, 빈도수) 튜플 리스트
        """
        all_words = []

        # 제목과 태그에서 키워드 추출
        for video in videos:
            # 제목에서 추출
            title = video.get("title", "")
            words = self._extract_keywords_from_text(title)
            all_words.extend(words)

            # 태그에서 추출
            tags = video.get("tags", [])
            for tag in tags:
                tag_words = self._extract_keywords_from_text(tag)
                all_words.extend(tag_words)

        # 빈도수 계산
        word_counts = Counter(all_words)

        # 불용어 제거 및 상위 N개 추출
        stopwords = self._get_korean_stopwords()
        filtered_keywords = [
            (word, count) for word, count in word_counts.most_common(top_n * 3)
            if word not in stopwords and len(word) > 1
        ]

        return filtered_keywords[:top_n]

    def analyze_optimal_duration(self, videos: List[Dict]) -> Dict[str, float]:
        """
        최적 영상 길이 분석

        Args:
            videos: 동영상 정보 리스트

        Returns:
            분석 결과 딕셔너리
        """
        durations = []

        for video in videos:
            duration_str = video.get("duration", "PT0S")
            seconds = self._parse_duration(duration_str)

            if seconds > 0:
                durations.append({
                    "seconds": seconds,
                    "view_count": video.get("view_count", 0),
                    "engagement_rate": self._calculate_engagement_rate(video)
                })

        if not durations:
            return {
                "average_seconds": 0,
                "recommended_min": 0,
                "recommended_max": 0
            }

        # 인기 영상들의 평균 길이 계산
        avg_seconds = sum(d["seconds"] for d in durations) / len(durations)

        # 참여율이 높은 영상들의 길이 범위 계산
        sorted_by_engagement = sorted(
            durations,
            key=lambda x: x["engagement_rate"],
            reverse=True
        )
        top_20_percent = sorted_by_engagement[:max(1, len(sorted_by_engagement) // 5)]

        top_durations = [d["seconds"] for d in top_20_percent]
        recommended_min = min(top_durations)
        recommended_max = max(top_durations)

        return {
            "average_seconds": round(avg_seconds, 2),
            "recommended_min_seconds": round(recommended_min, 2),
            "recommended_max_seconds": round(recommended_max, 2),
            "sample_size": len(durations)
        }

    def analyze_content_patterns(self, videos: List[Dict]) -> Dict:
        """
        콘텐츠 패턴 분석

        Args:
            videos: 동영상 정보 리스트

        Returns:
            패턴 분석 결과
        """
        patterns = {
            "title_patterns": self._analyze_title_patterns(videos),
            "engagement_metrics": self._analyze_engagement(videos),
            "posting_times": self._analyze_posting_times(videos)
        }

        return patterns

    def generate_content_suggestions(
        self,
        topic: str,
        region_code: str = "KR"
    ) -> Dict:
        """
        주제 기반 콘텐츠 제안 생성

        Args:
            topic: 영상 주제
            region_code: 국가 코드

        Returns:
            콘텐츠 제안 딕셔너리
        """
        # 트렌딩 동영상 가져오기
        videos = self.get_trending_videos(region_code=region_code)

        if not videos:
            logger.warning("No trending videos found, using fallback suggestions")
            return self._generate_fallback_suggestions(topic)

        # 바이럴 키워드 추출
        viral_keywords = self.extract_viral_keywords(videos)

        # 최적 길이 분석
        duration_analysis = self.analyze_optimal_duration(videos)

        # 콘텐츠 패턴 분석
        content_patterns = self.analyze_content_patterns(videos)

        # 제안 생성
        suggestions = {
            "topic": topic,
            "viral_keywords": [kw for kw, _ in viral_keywords[:10]],
            "recommended_duration_seconds": duration_analysis.get("average_seconds", 60),
            "optimal_duration_range": {
                "min": duration_analysis.get("recommended_min_seconds", 30),
                "max": duration_analysis.get("recommended_max_seconds", 180)
            },
            "title_suggestions": self._generate_title_suggestions(
                topic,
                viral_keywords,
                content_patterns["title_patterns"]
            ),
            "content_hooks": self._generate_content_hooks(viral_keywords),
            "posting_recommendation": content_patterns["posting_times"],
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "sample_size": len(videos),
                "region": region_code
            }
        }

        return suggestions

    # ========== 내부 헬퍼 함수 ==========

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        text = re.sub(r'[^\w\sㄱ-ㅎ가-힣]', ' ', text)
        words = text.split()

        # 2글자 이상인 단어만 추출
        keywords = [word.strip() for word in words if len(word.strip()) >= 2]

        return keywords

    def _get_korean_stopwords(self) -> set:
        """한국어 불용어 목록"""
        return {
            "그리고", "그러나", "그런데", "하지만", "그래서",
            "이것", "저것", "것들", "우리", "저희", "당신",
            "어떤", "무엇", "누가", "언제", "어디서", "어떻게",
            "합니다", "입니다", "있습니다", "없습니다",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"
        }

    def _parse_duration(self, duration_str: str) -> int:
        """ISO 8601 duration을 초 단위로 변환"""
        # PT1H2M30S 형식 파싱
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def _calculate_engagement_rate(self, video: Dict) -> float:
        """참여율 계산 (좋아요 + 댓글) / 조회수"""
        views = video.get("view_count", 0)
        if views == 0:
            return 0.0

        likes = video.get("like_count", 0)
        comments = video.get("comment_count", 0)

        return (likes + comments) / views

    def _analyze_title_patterns(self, videos: List[Dict]) -> Dict:
        """제목 패턴 분석"""
        patterns = {
            "avg_length": 0,
            "common_starts": [],
            "uses_numbers": 0,
            "uses_emojis": 0,
            "uses_questions": 0
        }

        if not videos:
            return patterns

        titles = [v.get("title", "") for v in videos]

        # 평균 길이
        patterns["avg_length"] = sum(len(t) for t in titles) / len(titles)

        # 숫자 사용
        patterns["uses_numbers"] = sum(1 for t in titles if re.search(r'\d', t))

        # 이모지 사용
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 이모티콘
            "\U0001F300-\U0001F5FF"  # 기호 & 픽토그램
            "\U0001F680-\U0001F6FF"  # 교통 & 지도
            "\U0001F1E0-\U0001F1FF"  # 국기
            "]+",
            flags=re.UNICODE
        )
        patterns["uses_emojis"] = sum(1 for t in titles if emoji_pattern.search(t))

        # 질문형 제목
        patterns["uses_questions"] = sum(1 for t in titles if "?" in t or "?" in t)

        # 시작 패턴
        first_words = [t.split()[0] if t.split() else "" for t in titles]
        word_counts = Counter(first_words)
        patterns["common_starts"] = [
            word for word, _ in word_counts.most_common(5) if word
        ]

        return patterns

    def _analyze_engagement(self, videos: List[Dict]) -> Dict:
        """참여도 분석"""
        if not videos:
            return {
                "avg_engagement_rate": 0,
                "avg_like_rate": 0,
                "avg_comment_rate": 0
            }

        engagement_rates = [self._calculate_engagement_rate(v) for v in videos]

        like_rates = []
        comment_rates = []

        for v in videos:
            views = v.get("view_count", 0)
            if views > 0:
                like_rates.append(v.get("like_count", 0) / views)
                comment_rates.append(v.get("comment_count", 0) / views)

        return {
            "avg_engagement_rate": sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0,
            "avg_like_rate": sum(like_rates) / len(like_rates) if like_rates else 0,
            "avg_comment_rate": sum(comment_rates) / len(comment_rates) if comment_rates else 0
        }

    def _analyze_posting_times(self, videos: List[Dict]) -> Dict:
        """게시 시간 분석"""
        if not videos:
            return {"recommended_hours": [], "recommendation": "오후 6-8시"}

        posting_hours = []

        for v in videos:
            published_at = v.get("published_at", "")
            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                # UTC를 KST로 변환 (UTC+9)
                dt_kst = dt + timedelta(hours=9)
                posting_hours.append(dt_kst.hour)
            except:
                continue

        if not posting_hours:
            return {"recommended_hours": [], "recommendation": "오후 6-8시"}

        # 가장 많이 게시되는 시간대
        hour_counts = Counter(posting_hours)
        top_hours = [hour for hour, _ in hour_counts.most_common(3)]

        # 권장 시간대 생성
        if top_hours:
            recommendation = f"오후 {top_hours[0] % 12 or 12}-{(top_hours[0] + 2) % 12 or 12}시"
        else:
            recommendation = "오후 6-8시"

        return {
            "recommended_hours": top_hours,
            "recommendation": recommendation,
            "distribution": dict(hour_counts.most_common(10))
        }

    def _generate_title_suggestions(
        self,
        topic: str,
        viral_keywords: List[Tuple[str, int]],
        title_patterns: Dict
    ) -> List[str]:
        """제목 제안 생성"""
        suggestions = []

        # 패턴 1: 숫자 + 주제 + 바이럴 키워드
        if viral_keywords:
            kw = viral_keywords[0][0]
            suggestions.append(f"🔥 {topic}의 비밀! {kw} 완벽 가이드")

        # 패턴 2: 질문형
        suggestions.append(f"❓ {topic}, 이렇게 하면 진짜 효과 있을까?")

        # 패턴 3: 숫자 리스트
        suggestions.append(f"✨ {topic} 시작 전 꼭 알아야 할 7가지")

        # 패턴 4: 충격 + 호기심
        suggestions.append(f"😱 {topic}의 충격적인 진실! 아무도 말해주지 않는 이야기")

        # 패턴 5: 비교/대결
        if len(viral_keywords) >= 2:
            kw1, kw2 = viral_keywords[0][0], viral_keywords[1][0]
            suggestions.append(f"⚡ {topic}: {kw1} vs {kw2} 완벽 비교")

        return suggestions[:5]

    def _generate_content_hooks(self, viral_keywords: List[Tuple[str, int]]) -> List[str]:
        """콘텐츠 훅(도입부) 제안"""
        hooks = [
            "오늘 소개할 내용, 끝까지 보시면 정말 놀라실 거예요!",
            "이 영상 하나면 충분합니다. 지금 바로 시작하세요!",
            "99%가 모르는 비밀, 지금 공개합니다!",
            "단 3분이면 이해할 수 있습니다. 집중하세요!",
            "이거 모르면 큰일납니다. 꼭 끝까지 보세요!"
        ]

        # 바이럴 키워드를 활용한 훅 추가
        if viral_keywords:
            kw = viral_keywords[0][0]
            hooks.append(f"{kw}에 대해 제대로 알려드립니다!")

        return hooks[:5]

    def _generate_fallback_suggestions(self, topic: str) -> Dict:
        """API 없이 기본 제안 생성"""
        return {
            "topic": topic,
            "viral_keywords": ["인기", "트렌드", "추천", "꿀팁", "비법"],
            "recommended_duration_seconds": 90,
            "optimal_duration_range": {"min": 60, "max": 180},
            "title_suggestions": [
                f"🔥 {topic} 완벽 가이드",
                f"❓ {topic}, 제대로 알고 계신가요?",
                f"✨ {topic} 시작 전 꼭 알아야 할 7가지",
                f"😱 {topic}의 충격적인 진실",
                f"⚡ {topic} 초보자를 위한 필수 팁"
            ],
            "content_hooks": [
                "오늘 소개할 내용, 끝까지 보시면 정말 놀라실 거예요!",
                "이 영상 하나면 충분합니다. 지금 바로 시작하세요!",
                "99%가 모르는 비밀, 지금 공개합니다!"
            ],
            "posting_recommendation": {
                "recommended_hours": [18, 19, 20],
                "recommendation": "오후 6-8시"
            },
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "sample_size": 0,
                "region": "KR",
                "mode": "fallback"
            }
        }


# 편의 함수
def analyze_youtube_trends(
    topic: str,
    api_key: Optional[str] = None,
    region_code: str = "KR"
) -> Dict:
    """
    유튜브 트렌드 분석 및 콘텐츠 제안 생성

    Args:
        topic: 영상 주제
        api_key: 유튜브 API 키
        region_code: 국가 코드

    Returns:
        분석 결과 및 제안
    """
    analyzer = YouTubeTrendAnalyzer(api_key)
    return analyzer.generate_content_suggestions(topic, region_code)
