# thumbnail_generator.py 한글 폰트 수정 패치
# 이 코드를 thumbnail_generator.py에 추가하세요

def _get_korean_font(self, size: int):
    """
    한글 지원 폰트 로드

    Args:
        size: 폰트 크기

    Returns:
        ImageFont 객체
    """
    # Windows 한글 폰트 경로 목록 (우선순위 순)
    korean_fonts = [
        "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
        "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
        "C:/Windows/Fonts/NanumGothic.ttf", # 나눔고딕
        "C:/Windows/Fonts/gulim.ttc",       # 굴림
        "C:/Windows/Fonts/batang.ttc",      # 바탕
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux
    ]

    # 사용 가능한 폰트 찾기
    for font_path in korean_fonts:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue

    # 모든 폰트 실패 시 기본 폰트 (한글 표시 안 됨)
    logger.warning("Korean font not found. Text may not display correctly.")
    return ImageFont.load_default()


# 수정할 부분들:

# 1. _add_text 메소드 (line 305-310)
# 기존:
#     try:
#         # Windows 기본 폰트
#         font = ImageFont.truetype("arial.ttf", self.font_sizes["title"])
#     except:
#         font = ImageFont.load_default()

# 수정:
#     font = self._get_korean_font(self.font_sizes["title"])


# 2. generate_viral_thumbnail 메소드의 키워드 폰트 (line 435-437)
# 기존:
#             try:
#                 keyword_font = ImageFont.truetype("arial.ttf", self.font_sizes["keyword"])
#             except:
#                 keyword_font = ImageFont.load_default()

# 수정:
#             keyword_font = self._get_korean_font(self.font_sizes["keyword"])


# 3. _add_emotion_emoji 메소드 (line 478-481)
# 기존:
#         try:
#             emoji_font = ImageFont.truetype("seguiemj.ttf", 150)  # Windows 이모지 폰트
#         except:
#             emoji_font = ImageFont.load_default()

# 수정:
#         try:
#             emoji_font = ImageFont.truetype("seguiemj.ttf", 150)
#         except:
#             emoji_font = self._get_korean_font(150)


# 4. _add_cta_text 메소드 (line 510-512)
# 기존:
#         try:
#             cta_font = ImageFont.truetype("arial.ttf", 60)
#         except:
#             cta_font = ImageFont.load_default()

# 수정:
#         cta_font = self._get_korean_font(60)
