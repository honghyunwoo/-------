"""
한국형 템플릿 데이터
"""

KOREAN_TEMPLATES = [
    {
        "name": "맛집 홍보",
        "description": "음식점, 카페 홍보용 템플릿",
        "category": "음식점",
        "tags": ["맛집", "카페", "레스토랑", "음식"],
        "parameters": {
            "video_aspect": "9:16",
            "video_concat_mode": "random",
            "font_name": "NanumGothic-Bold.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#FF5733",
            "font_size": 65,
            "stroke_color": "#000000",
            "stroke_width": 2.0,
            "bgm_type": "upbeat",
            "voice_name": "ko-KR-SunHiNeural"
        }
    },
    {
        "name": "쇼핑몰 상품소개",
        "description": "온라인 쇼핑몰 상품 홍보 템플릿",
        "category": "쇼핑몰",
        "tags": ["쇼핑", "상품", "판매", "이커머스"],
        "parameters": {
            "video_aspect": "1:1",
            "video_concat_mode": "sequential",
            "font_name": "Pretendard-Bold.ttf",
            "text_fore_color": "#000000",
            "text_background_color": "#FFEB3B",
            "font_size": 55,
            "stroke_color": "#FFFFFF",
            "stroke_width": 1.5,
            "bgm_type": "trendy",
            "voice_name": "ko-KR-InJoonNeural"
        }
    },
    {
        "name": "교육 강의",
        "description": "온라인 교육 콘텐츠용 템플릿",
        "category": "교육",
        "tags": ["교육", "강의", "학습", "튜토리얼"],
        "parameters": {
            "video_aspect": "16:9",
            "video_concat_mode": "sequential",
            "font_name": "NotoSansKR-Medium.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#2196F3",
            "font_size": 50,
            "stroke_color": "#000000",
            "stroke_width": 1.0,
            "bgm_type": "calm",
            "voice_name": "ko-KR-SunHiNeural"
        }
    },
    {
        "name": "부동산 매물소개",
        "description": "부동산 매물 홍보용 템플릿",
        "category": "부동산",
        "tags": ["부동산", "아파트", "주택", "매물"],
        "parameters": {
            "video_aspect": "16:9",
            "video_concat_mode": "sequential",
            "font_name": "SpoqaHanSansNeo-Bold.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#4CAF50",
            "font_size": 58,
            "stroke_color": "#000000",
            "stroke_width": 1.8,
            "bgm_type": "professional",
            "voice_name": "ko-KR-InJoonNeural"
        }
    },
    {
        "name": "뷰티 제품",
        "description": "화장품, 뷰티 제품 홍보 템플릿",
        "category": "뷰티",
        "tags": ["화장품", "뷰티", "스킨케어", "메이크업"],
        "parameters": {
            "video_aspect": "9:16",
            "video_concat_mode": "random",
            "font_name": "GmarketSans-Bold.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#E91E63",
            "font_size": 60,
            "stroke_color": "#000000",
            "stroke_width": 1.5,
            "bgm_type": "elegant",
            "voice_name": "ko-KR-SunHiNeural"
        }
    },
    {
        "name": "피트니스 운동",
        "description": "헬스, 요가, 운동 콘텐츠용 템플릿",
        "category": "피트니스",
        "tags": ["운동", "헬스", "요가", "피트니스"],
        "parameters": {
            "video_aspect": "9:16",
            "video_concat_mode": "sequential",
            "font_name": "BlackHanSans-Regular.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#FF9800",
            "font_size": 70,
            "stroke_color": "#000000",
            "stroke_width": 2.5,
            "bgm_type": "energetic",
            "voice_name": "ko-KR-InJoonNeural"
        }
    },
    {
        "name": "여행 브이로그",
        "description": "여행 콘텐츠용 템플릿",
        "category": "여행",
        "tags": ["여행", "브이로그", "관광", "휴가"],
        "parameters": {
            "video_aspect": "16:9",
            "video_concat_mode": "random",
            "font_name": "Cafe24Ssurround.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#00BCD4",
            "font_size": 55,
            "stroke_color": "#000000",
            "stroke_width": 1.5,
            "bgm_type": "adventure",
            "voice_name": "ko-KR-SunHiNeural"
        }
    },
    {
        "name": "게임 하이라이트",
        "description": "게임 플레이 하이라이트 영상 템플릿",
        "category": "게임",
        "tags": ["게임", "e스포츠", "하이라이트", "플레이"],
        "parameters": {
            "video_aspect": "16:9",
            "video_concat_mode": "sequential",
            "font_name": "DOSGothic.ttf",
            "text_fore_color": "#00FF00",
            "text_background_color": "#000000",
            "font_size": 65,
            "stroke_color": "#FFFFFF",
            "stroke_width": 2.0,
            "bgm_type": "epic",
            "voice_name": "ko-KR-InJoonNeural"
        }
    },
    {
        "name": "요리 레시피",
        "description": "요리 레시피 소개 영상 템플릿",
        "category": "요리",
        "tags": ["요리", "레시피", "쿠킹", "음식"],
        "parameters": {
            "video_aspect": "1:1",
            "video_concat_mode": "sequential",
            "font_name": "CookieRun-Bold.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#FF6B6B",
            "font_size": 60,
            "stroke_color": "#000000",
            "stroke_width": 1.8,
            "bgm_type": "cheerful",
            "voice_name": "ko-KR-SunHiNeural"
        }
    },
    {
        "name": "뉴스 브리핑",
        "description": "뉴스, 정보 전달용 템플릿",
        "category": "뉴스",
        "tags": ["뉴스", "정보", "브리핑", "리포트"],
        "parameters": {
            "video_aspect": "16:9",
            "video_concat_mode": "sequential",
            "font_name": "NanumMyeongjo-Bold.ttf",
            "text_fore_color": "#FFFFFF",
            "text_background_color": "#212121",
            "font_size": 52,
            "stroke_color": "#FFFFFF",
            "stroke_width": 1.0,
            "bgm_type": "news",
            "voice_name": "ko-KR-InJoonNeural"
        }
    }
]

# 한국형 폰트 목록
KOREAN_FONTS = [
    "NanumGothic-Bold.ttf",
    "NanumMyeongjo-Bold.ttf",
    "NotoSansKR-Bold.ttf",
    "NotoSansKR-Medium.ttf",
    "Pretendard-Bold.ttf",
    "Pretendard-Regular.ttf",
    "SpoqaHanSansNeo-Bold.ttf",
    "GmarketSans-Bold.ttf",
    "BlackHanSans-Regular.ttf",
    "Cafe24Ssurround.ttf",
    "CookieRun-Bold.ttf",
    "DOSGothic.ttf"
]

# BGM 타입별 설명
BGM_TYPES = {
    "upbeat": "밝고 경쾌한 음악",
    "trendy": "트렌디하고 현대적인 음악",
    "calm": "차분하고 편안한 음악",
    "professional": "전문적이고 신뢰감 있는 음악",
    "elegant": "우아하고 세련된 음악",
    "energetic": "활기차고 에너지 넘치는 음악",
    "adventure": "모험적이고 신나는 음악",
    "epic": "웅장하고 강렬한 음악",
    "cheerful": "즐겁고 유쾌한 음악",
    "news": "뉴스 브리핑용 배경음악"
}