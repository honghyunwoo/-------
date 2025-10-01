#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SEO 최적화 엔진

이 모듈은 유튜브 영상의 SEO를 최적화합니다:
1. 제목 최적화 (키워드, 길이, 클릭 유발)
2. 설명 최적화 (키워드 밀도, 구조화, CTR)
3. 태그 생성 (관련성, 검색량, 다양성)
4. 해시태그 최적화 (3-5개, 관련성 높은)
5. 카테고리 자동 선택
6. 게시 시간 최적화 (시간대별 조회수 분석)
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class SEOOptimizer:
    """SEO 최적화 엔진"""

    def __init__(self):
        """초기화"""
        # 유튜브 제목 최적 길이
        self.title_optimal_length = (50, 70)  # 문자 수
        self.title_max_length = 100
        
        # 유튜브 설명 최적 길이
        self.description_optimal_length = (200, 300)  # 문자 수
        self.description_max_length = 5000
        
        # 태그 설정
        self.max_tags = 15  # 유튜브 권장: 10-15개
        self.tag_max_length = 30  # 개당 최대 길이
        
        # 해시태그 설정
        self.hashtag_count = (3, 5)  # 3-5개 권장
        
        # 유튜브 카테고리 ID
        self.categories = {
            "교육": 27,
            "과학기술": 28,
            "엔터테인먼트": 24,
            "음악": 10,
            "게임": 20,
            "뉴스": 25,
            "스포츠": 17,
            "자동차": 2,
            "여행": 19,
            "코미디": 23,
            "하우투": 26,
            "요리": 26
        }
        
        # 키워드 강도 가중치
        self.keyword_weights = {
            "primary": 3.0,    # 주요 키워드
            "secondary": 2.0,  # 보조 키워드
            "related": 1.0     # 관련 키워드
        }
        
        # 최적 게시 시간 (한국 시간 기준)
        self.optimal_posting_times = {
            "weekday": [
                (6, 9),    # 출근 시간
                (12, 14),  # 점심 시간
                (18, 23)   # 퇴근 후~취침 전
            ],
            "weekend": [
                (10, 12),  # 오전
                (14, 16),  # 오후
                (19, 23)   # 저녁
            ]
        }

    def optimize_title(
        self,
        topic: str,
        keywords: List[str],
        viral_keywords: Optional[List[Tuple[str, int]]] = None,
        style: str = "curiosity"
    ) -> Dict[str, any]:
        """
        제목 최적화

        Args:
            topic: 주제
            keywords: 키워드 리스트
            viral_keywords: 바이럴 키워드 (선택)
            style: 스타일 (curiosity, question, number, benefit)

        Returns:
            최적화된 제목 정보
        """
        # 1. 기본 제목 템플릿
        templates = self._get_title_templates(style)
        
        # 2. 바이럴 키워드 추출 (우선순위 높음)
        top_keywords = []
        if viral_keywords:
            top_keywords = [kw[0] for kw in viral_keywords[:3]]
        else:
            top_keywords = keywords[:3] if keywords else [topic]
        
        # 3. 제목 생성
        generated_titles = []
        for template in templates[:5]:  # 상위 5개 템플릿
            title = self._fill_title_template(template, topic, top_keywords)
            score = self._score_title(title, keywords)
            
            generated_titles.append({
                "title": title,
                "length": len(title),
                "score": score,
                "keywords_count": self._count_keywords_in_text(title, keywords),
                "optimal_length": self.title_optimal_length[0] <= len(title) <= self.title_optimal_length[1]
            })
        
        # 4. 점수 기준 정렬
        generated_titles.sort(key=lambda x: x["score"], reverse=True)
        
        best_title = generated_titles[0]
        
        logger.info(f"Optimized title: {best_title['title'][:50]}... (score: {best_title['score']:.2f})")
        
        return {
            "best_title": best_title["title"],
            "score": best_title["score"],
            "alternatives": [t["title"] for t in generated_titles[1:4]],
            "analysis": {
                "length": best_title["length"],
                "keywords_included": best_title["keywords_count"],
                "optimal_length": best_title["optimal_length"],
                "estimated_ctr": self._estimate_ctr(best_title["score"])
            }
        }

    def _get_title_templates(self, style: str) -> List[str]:
        """제목 템플릿 반환"""
        templates = {
            "curiosity": [
                "{topic}의 숨겨진 비밀",
                "아무도 말하지 않는 {topic}의 진실",
                "{topic}에 대해 당신이 몰랐던 것",
                "{keyword}로 {topic} 완전히 이해하기",
                "{topic}: 전문가들이 숨기는 {keyword}"
            ],
            "question": [
                "{topic}이 정말 효과가 있을까?",
                "{topic}으로 {keyword}가 가능한가?",
                "왜 모두가 {topic}에 열광하는가?",
                "{topic} vs {keyword}: 어떤 게 더 나을까?",
                "{topic}을 시작하기 전에 알아야 할 것은?"
            ],
            "number": [
                "{topic}을 위한 {number}가지 방법",
                "{number}분 안에 {topic} 마스터하기",
                "{topic}의 {number}가지 놀라운 사실",
                "{number}일 {topic} 챌린지 결과",
                "{topic}으로 {number}배 더 나아지는 법"
            ],
            "benefit": [
                "{topic}으로 {keyword}하는 확실한 방법",
                "{topic} 완벽 가이드: {keyword}까지",
                "{keyword}를 위한 최고의 {topic} 전략",
                "{topic}으로 {keyword} 달성하기",
                "초보자를 위한 {topic} {keyword} 가이드"
            ]
        }
        
        return templates.get(style, templates["curiosity"])

    def _fill_title_template(
        self,
        template: str,
        topic: str,
        keywords: List[str]
    ) -> str:
        """템플릿에 값 채우기"""
        import random
        
        keyword = keywords[0] if keywords else "팁"
        number = random.choice(["3", "5", "7", "10"])
        
        title = template.replace("{topic}", topic)
        title = title.replace("{keyword}", keyword)
        title = title.replace("{number}", number)
        
        # 길이 조정
        if len(title) > self.title_max_length:
            title = title[:self.title_max_length-3] + "..."
        
        return title

    def _score_title(self, title: str, keywords: List[str]) -> float:
        """
        제목 점수 계산 (0-100)

        평가 기준:
        - 길이 (20점)
        - 키워드 포함 (30점)
        - 숫자 포함 (10점)
        - 질문 형식 (10점)
        - 감정 단어 (15점)
        - 특수 문자 사용 (5점)
        - 대문자 비율 (10점)
        """
        score = 0.0
        
        # 1. 길이 점수 (20점)
        length = len(title)
        if self.title_optimal_length[0] <= length <= self.title_optimal_length[1]:
            score += 20
        elif length < self.title_optimal_length[0]:
            score += 15 * (length / self.title_optimal_length[0])
        else:
            score += 15 * (self.title_max_length / length)
        
        # 2. 키워드 포함 (30점)
        keyword_count = self._count_keywords_in_text(title, keywords)
        score += min(keyword_count * 10, 30)
        
        # 3. 숫자 포함 (10점)
        if re.search(r'\d+', title):
            score += 10
        
        # 4. 질문 형식 (10점)
        if '?' in title or '인가' in title or '일까' in title:
            score += 10
        
        # 5. 감정 단어 (15점)
        emotion_words = ["충격", "놀라운", "비밀", "진짜", "완전", "최고", "최악"]
        emotion_count = sum(1 for word in emotion_words if word in title)
        score += min(emotion_count * 5, 15)
        
        # 6. 특수 문자 (5점)
        if any(char in title for char in ['!', ':', '-', '→']):
            score += 5
        
        # 7. 대문자 비율 (10점) - 한글에는 해당 없음, 영어 제목용
        upper_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
        if 0.05 <= upper_ratio <= 0.15:
            score += 10
        
        return min(score, 100.0)

    def _count_keywords_in_text(self, text: str, keywords: List[str]) -> int:
        """텍스트 내 키워드 개수 카운트"""
        text_lower = text.lower()
        return sum(1 for keyword in keywords if keyword.lower() in text_lower)

    def _estimate_ctr(self, title_score: float) -> float:
        """제목 점수로 예상 CTR 계산"""
        # 선형 매핑: 점수 0-100 → CTR 2-15%
        base_ctr = 2.0
        max_ctr = 15.0
        return base_ctr + (max_ctr - base_ctr) * (title_score / 100.0)

    def generate_description(
        self,
        title: str,
        topic: str,
        keywords: List[str],
        script_summary: Optional[str] = None,
        include_timestamps: bool = True
    ) -> Dict[str, str]:
        """
        설명(Description) 생성

        Args:
            title: 제목
            topic: 주제
            keywords: 키워드 리스트
            script_summary: 스크립트 요약 (선택)
            include_timestamps: 타임스탬프 포함 여부

        Returns:
            최적화된 설명 정보
        """
        # 1. 오프닝 (첫 150자가 가장 중요)
        opening = f"{title}\n\n"
        opening += f"이 영상에서는 {topic}에 대해 자세히 알아봅니다.\n"
        if keywords:
            opening += f"핵심 내용: {', '.join(keywords[:5])}\n\n"
        
        # 2. 메인 설명
        main_desc = ""
        if script_summary:
            main_desc += f"📋 요약:\n{script_summary}\n\n"
        else:
            main_desc += f"📋 이 영상을 통해 {topic}의 핵심을 배울 수 있습니다.\n\n"
        
        # 3. 타임스탬프 (선택)
        timestamps = ""
        if include_timestamps:
            timestamps += "⏰ 타임스탬프:\n"
            timestamps += "00:00 인트로\n"
            timestamps += "00:30 주요 내용\n"
            timestamps += "05:00 실전 팁\n"
            timestamps += "08:00 마무리\n\n"
        
        # 4. 관련 키워드 섹션
        keyword_section = "🔍 관련 키워드:\n"
        keyword_section += f"{', '.join(keywords[:10])}\n\n"
        
        # 5. CTA (Call To Action)
        cta = "👍 이 영상이 도움이 되었다면 좋아요와 구독 부탁드립니다!\n"
        cta += "🔔 알림 설정을 해두시면 새로운 영상을 놓치지 않으실 수 있어요.\n\n"
        
        # 6. 해시태그
        hashtags = self.generate_hashtags(topic, keywords)
        hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
        
        # 전체 설명 조합
        full_description = opening + main_desc + timestamps + keyword_section + cta + hashtag_str
        
        # 길이 체크 및 조정
        if len(full_description) > self.description_max_length:
            full_description = full_description[:self.description_max_length-20] + "\n..."
        
        logger.info(f"Generated description: {len(full_description)} characters")
        
        return {
            "full_description": full_description,
            "opening": opening,
            "length": len(full_description),
            "keyword_density": self._calculate_keyword_density(full_description, keywords),
            "readability_score": self._calculate_readability(full_description)
        }

    def generate_tags(
        self,
        topic: str,
        keywords: List[str],
        viral_keywords: Optional[List[Tuple[str, int]]] = None
    ) -> List[str]:
        """
        태그 생성

        Args:
            topic: 주제
            keywords: 키워드 리스트
            viral_keywords: 바이럴 키워드 (선택)

        Returns:
            태그 리스트
        """
        tags = []
        
        # 1. 주요 주제 태그
        tags.append(topic)
        
        # 2. 키워드 태그
        for keyword in keywords[:8]:
            if len(keyword) <= self.tag_max_length:
                tags.append(keyword)
        
        # 3. 바이럴 키워드 태그 (우선순위 높음)
        if viral_keywords:
            for kw, _ in viral_keywords[:5]:
                if kw not in tags and len(kw) <= self.tag_max_length:
                    tags.append(kw)
        
        # 4. 관련 조합 태그
        if len(keywords) >= 2:
            combined = f"{keywords[0]} {keywords[1]}"
            if len(combined) <= self.tag_max_length:
                tags.append(combined)
        
        # 5. 장르/카테고리 태그
        genre_tags = ["교육", "가이드", "팁", "하우투", "튜토리얼"]
        for tag in genre_tags:
            if len(tags) < self.max_tags:
                tags.append(tag)
        
        # 중복 제거 및 길이 제한
        tags = list(dict.fromkeys(tags))  # 순서 유지하며 중복 제거
        tags = tags[:self.max_tags]
        
        logger.info(f"Generated {len(tags)} tags")
        return tags

    def generate_hashtags(
        self,
        topic: str,
        keywords: List[str]
    ) -> List[str]:
        """
        해시태그 생성 (3-5개)

        Args:
            topic: 주제
            keywords: 키워드 리스트

        Returns:
            해시태그 리스트
        """
        hashtags = []
        
        # 1. 주제 해시태그
        hashtags.append(topic.replace(" ", ""))
        
        # 2. 상위 키워드 해시태그
        for keyword in keywords[:4]:
            clean_keyword = keyword.replace(" ", "")
            if clean_keyword and clean_keyword not in hashtags:
                hashtags.append(clean_keyword)
        
        # 3-5개로 제한
        hashtags = hashtags[:5]
        
        return hashtags

    def select_category(self, topic: str, keywords: List[str]) -> Dict[str, any]:
        """
        카테고리 자동 선택

        Args:
            topic: 주제
            keywords: 키워드 리스트

        Returns:
            카테고리 정보
        """
        # 키워드 기반 카테고리 매칭
        text = f"{topic} {' '.join(keywords)}".lower()
        
        category_scores = {}
        for category_name, category_id in self.categories.items():
            score = text.count(category_name.lower())
            if score > 0:
                category_scores[category_name] = score
        
        # 가장 높은 점수의 카테고리 선택
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return {
                "category_name": best_category,
                "category_id": self.categories[best_category],
                "confidence": category_scores[best_category]
            }
        
        # 기본값: 교육
        return {
            "category_name": "교육",
            "category_id": 27,
            "confidence": 0
        }

    def suggest_posting_time(self, target_audience: str = "general") -> Dict[str, any]:
        """
        최적 게시 시간 제안

        Args:
            target_audience: 타겟 오디언스 (general, student, worker)

        Returns:
            게시 시간 제안
        """
        now = datetime.now()
        is_weekend = now.weekday() >= 5  # 토요일(5), 일요일(6)
        
        # 주중/주말 구분
        time_slots = self.optimal_posting_times["weekend" if is_weekend else "weekday"]
        
        # 현재 시간과 가장 가까운 최적 시간 찾기
        current_hour = now.hour
        next_optimal_time = None
        
        for start_hour, end_hour in time_slots:
            if current_hour < start_hour:
                # 오늘 중 다음 최적 시간
                next_optimal_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                break
        
        if not next_optimal_time:
            # 오늘의 최적 시간이 모두 지났으면 내일 첫 시간
            tomorrow = now + timedelta(days=1)
            first_slot = self.optimal_posting_times["weekend" if tomorrow.weekday() >= 5 else "weekday"][0]
            next_optimal_time = tomorrow.replace(hour=first_slot[0], minute=0, second=0, microsecond=0)
        
        logger.info(f"Suggested posting time: {next_optimal_time}")
        
        return {
            "recommended_time": next_optimal_time.strftime("%Y-%m-%d %H:%M"),
            "day_type": "주말" if is_weekend else "주중",
            "time_slot": f"{next_optimal_time.hour}:00",
            "reason": self._get_posting_time_reason(next_optimal_time.hour, is_weekend)
        }

    def _get_posting_time_reason(self, hour: int, is_weekend: bool) -> str:
        """게시 시간 이유 설명"""
        if 6 <= hour < 9:
            return "출근/등교 시간대 - 이동 중 영상 시청 가능성 높음"
        elif 12 <= hour < 14:
            return "점심 시간 - 휴식 시간에 영상 소비 증가"
        elif 18 <= hour < 20:
            return "퇴근 시간 - 귀가 중 영상 시청 증가"
        elif 20 <= hour < 23:
            return "저녁 시간 - 하루 중 유튜브 사용량이 가장 높은 시간대"
        elif is_weekend and 10 <= hour < 12:
            return "주말 오전 - 여유로운 시간에 긴 영상 시청 가능"
        else:
            return "일반 시청 시간대"

    def _calculate_keyword_density(self, text: str, keywords: List[str]) -> float:
        """키워드 밀도 계산 (%%)"""
        if not text or not keywords:
            return 0.0
        
        total_words = len(text.split())
        keyword_count = self._count_keywords_in_text(text, keywords)
        
        return (keyword_count / total_words) * 100 if total_words > 0 else 0.0

    def _calculate_readability(self, text: str) -> float:
        """가독성 점수 계산 (0-100, 높을수록 읽기 쉬움)"""
        if not text:
            return 0.0
        
        # 간단한 가독성 지표
        sentences = text.count('.') + text.count('!') + text.count('?')
        words = len(text.split())
        
        if sentences == 0:
            return 50.0
        
        avg_words_per_sentence = words / sentences
        
        # 이상적인 문장당 단어 수: 15-20
        if 15 <= avg_words_per_sentence <= 20:
            return 100.0
        elif avg_words_per_sentence < 10:
            return 70.0
        elif avg_words_per_sentence < 25:
            return 85.0
        else:
            return 60.0


def optimize_video_seo(
    topic: str,
    keywords: List[str],
    viral_keywords: Optional[List[Tuple[str, int]]] = None,
    script_summary: Optional[str] = None
) -> Dict[str, any]:
    """
    편의 함수: 영상 SEO 종합 최적화

    Args:
        topic: 주제
        keywords: 키워드 리스트
        viral_keywords: 바이럴 키워드 (선택)
        script_summary: 스크립트 요약 (선택)

    Returns:
        SEO 최적화 결과
    """
    optimizer = SEOOptimizer()
    
    # 1. 제목 최적화
    title_result = optimizer.optimize_title(topic, keywords, viral_keywords)
    
    # 2. 설명 생성
    description_result = optimizer.generate_description(
        title_result["best_title"],
        topic,
        keywords,
        script_summary
    )
    
    # 3. 태그 생성
    tags = optimizer.generate_tags(topic, keywords, viral_keywords)
    
    # 4. 카테고리 선택
    category = optimizer.select_category(topic, keywords)
    
    # 5. 게시 시간 제안
    posting_time = optimizer.suggest_posting_time()
    
    return {
        "title": title_result["best_title"],
        "title_analysis": title_result["analysis"],
        "description": description_result["full_description"],
        "description_analysis": {
            "length": description_result["length"],
            "keyword_density": description_result["keyword_density"],
            "readability": description_result["readability_score"]
        },
        "tags": tags,
        "category": category,
        "posting_time": posting_time,
        "overall_score": title_result["score"]
    }
