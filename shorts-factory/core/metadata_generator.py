"""
메타데이터 생성 모듈
YouTube 업로드용 제목, 설명, 태그 생성
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False


@dataclass
class VideoMetadata:
    """영상 메타데이터"""
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    category: str = "22"  # People & Blogs
    privacy: str = "public"  # public, private, unlisted
    scheduled_time: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "category": self.category,
            "privacy": self.privacy,
            "scheduled_time": self.scheduled_time
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoMetadata':
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            hashtags=data.get("hashtags", []),
            category=data.get("category", "22"),
            privacy=data.get("privacy", "public"),
            scheduled_time=data.get("scheduled_time")
        )


@dataclass
class MetadataTemplate:
    """메타데이터 템플릿"""
    title_template: str = "{keyword} - {author} #shorts"
    description_template: str = """"{quote}"
- {author}, {source}

{hashtags}

📌 매일 스토아 철학으로 삶의 지혜를 전합니다.
구독과 좋아요 부탁드립니다!
"""
    base_tags: List[str] = field(default_factory=lambda: [
        "shorts", "동기부여", "자기계발", "명언", "스토아철학"
    ])
    base_hashtags: List[str] = field(default_factory=lambda: [
        "#shorts", "#동기부여", "#명언", "#스토아철학"
    ])


class MetadataGenerator:
    """메타데이터 생성기"""

    # 채널별 기본 템플릿
    CHANNEL_TEMPLATES = {
        "stoic": MetadataTemplate(
            title_template="{keyword} - {author} #shorts #스토아",
            description_template=""""{quote}"
- {author}, {source}

{hashtags}

📌 매일 스토아 - 고대 철학의 지혜로 오늘을 살아가세요.
🔔 구독하고 매일 새로운 명언을 만나보세요!
""",
            base_tags=["shorts", "동기부여", "자기계발", "명언", "스토아철학",
                      "에픽테토스", "마르쿠스 아우렐리우스", "세네카", "철학"],
            base_hashtags=["#shorts", "#동기부여", "#명언", "#스토아철학", "#자기계발"]
        ),
        "english": MetadataTemplate(
            title_template="{expression} - 영어표현 #shorts",
            description_template="""{expression}
{meaning}

{example}

{hashtags}

📚 매일 1분 영어 - 실생활에서 바로 쓰는 영어 표현!
""",
            base_tags=["shorts", "영어공부", "영어표현", "영어회화", "English",
                      "영어학습", "일상영어", "실용영어"],
            base_hashtags=["#shorts", "#영어공부", "#영어표현", "#영어회화"]
        )
    }

    # 테마별 추가 태그
    THEME_TAGS = {
        "역경": ["역경극복", "시련", "고난", "성장", "회복력"],
        "마음": ["마음공부", "내면", "평화", "명상", "정신건강"],
        "시간": ["시간관리", "하루", "인생", "오늘", "현재"],
        "통제": ["자기통제", "절제", "규율", "습관", "자기관리"],
        "죽음": ["삶과죽음", "인생철학", "유한성", "memento mori"],
        "미덕": ["덕", "선함", "도덕", "인격", "성품"],
        "행복": ["행복", "기쁨", "만족", "감사", "긍정"]
    }

    def __init__(self, templates_path: Path = None, api_key: str = None):
        self.templates_path = templates_path
        self.api_key = api_key
        self.templates = self._load_templates()

        # Google Gemini API 설정
        if api_key and HAS_GENAI:
            genai.configure(api_key=api_key)
            # gemini-3-flash-preview: 더 높은 무료 쿼터 + 안정적
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None

    def _load_templates(self) -> Dict[str, MetadataTemplate]:
        """템플릿 로드"""
        if self.templates_path and Path(self.templates_path).exists():
            try:
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    templates = {}
                    for channel, template_data in data.items():
                        templates[channel] = MetadataTemplate(
                            title_template=template_data.get("title_template", ""),
                            description_template=template_data.get("description_template", ""),
                            base_tags=template_data.get("base_tags", []),
                            base_hashtags=template_data.get("base_hashtags", [])
                        )
                    return templates
            except (json.JSONDecodeError, KeyError):
                pass

        return self.CHANNEL_TEMPLATES.copy()

    def generate(
        self,
        script: 'Script',
        quote: 'Quote' = None,
        channel: str = "stoic",
        use_ai: bool = False
    ) -> VideoMetadata:
        """메타데이터 생성"""
        template = self.templates.get(channel, self.templates.get("stoic"))

        if use_ai and self.model and HAS_GENAI:
            return self._generate_with_ai(script, quote, channel)

        # 템플릿 기반 생성
        return self._generate_from_template(script, quote, template, channel)

    def _generate_from_template(
        self,
        script: 'Script',
        quote: 'Quote',
        template: MetadataTemplate,
        channel: str
    ) -> VideoMetadata:
        """템플릿에서 메타데이터 생성"""
        # 키워드 추출 (간단한 방식)
        keyword = self._extract_keyword(script, quote)

        # 변수 준비
        variables = {
            "keyword": keyword,
            "author": quote.author if quote else "",
            "source": quote.source if quote else "",
            "quote": quote.text if quote else script.quote_text,
            "expression": getattr(script, 'expression', ''),
            "meaning": getattr(script, 'meaning', ''),
            "example": getattr(script, 'example', ''),
            "hashtags": " ".join(template.base_hashtags)
        }

        # 제목 생성 (50자 제한)
        title = template.title_template.format(**variables)
        if len(title) > 50:
            title = title[:47] + "..."

        # 설명 생성
        description = template.description_template.format(**variables)

        # 태그 생성
        tags = template.base_tags.copy()
        if quote and hasattr(quote, 'themes'):
            for theme in quote.themes:
                tags.extend(self.THEME_TAGS.get(theme, []))
        tags = list(set(tags))[:30]  # YouTube 태그 제한

        # 해시태그
        hashtags = template.base_hashtags.copy()
        if quote and hasattr(quote, 'themes'):
            for theme in quote.themes:
                hashtags.append(f"#{theme}")
        hashtags = list(set(hashtags))[:10]

        return VideoMetadata(
            title=title,
            description=description,
            tags=tags,
            hashtags=hashtags
        )

    def _extract_keyword(self, script: 'Script', quote: 'Quote') -> str:
        """스크립트에서 핵심 키워드 추출"""
        # 훅에서 키워드 추출 시도
        if hasattr(script, 'hook') and script.hook:
            # 질문형이면 질문 핵심어
            hook = script.hook
            if '?' in hook:
                # 의문사 뒤의 단어들 추출
                words = re.findall(r'[가-힣]{2,}', hook)
                if words:
                    return words[-1]

        # 테마에서 추출
        if quote and hasattr(quote, 'themes') and quote.themes:
            theme_keywords = {
                "역경": "역경 극복",
                "마음": "마음의 평화",
                "시간": "오늘의 가치",
                "통제": "자기 통제",
                "죽음": "삶의 의미",
                "미덕": "진정한 덕",
                "행복": "진정한 행복"
            }
            return theme_keywords.get(quote.themes[0], quote.themes[0])

        # 저자 이름 사용
        if quote and quote.author:
            return f"{quote.author}의 지혜"

        return "스토아 명언"

    def _generate_with_ai(
        self,
        script: 'Script',
        quote: 'Quote',
        channel: str
    ) -> VideoMetadata:
        """AI로 메타데이터 생성 (Google Gemini API)"""
        prompt = f"""다음 YouTube Shorts 스크립트의 메타데이터를 생성해주세요.

스크립트:
{script.full_text if hasattr(script, 'full_text') else str(script)}

명언: {quote.text if quote else 'N/A'}
저자: {quote.author if quote else 'N/A'}
채널: {channel}

다음 JSON 형식으로 응답해주세요:
{{
    "title": "50자 이내의 매력적인 제목 (#shorts 포함)",
    "description": "YouTube 설명란",
    "tags": ["태그1", "태그2", ...],
    "hashtags": ["#해시태그1", "#해시태그2", ...]
}}

규칙:
1. 제목은 50자 이내, 호기심을 유발하는 문구
2. #shorts 태그 필수
3. 태그는 15-20개
4. 해시태그는 5-10개
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7
                )
            )

            response_text = response.text

            # JSON 파싱
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return VideoMetadata.from_dict(data)

        except Exception as e:
            logger.warning(f"AI 메타데이터 생성 실패: {e}")

        # 실패시 템플릿 사용
        return self._generate_from_template(
            script, quote,
            self.templates.get(channel, self.templates.get("stoic")),
            channel
        )

    def save(self, metadata: VideoMetadata, output_path: Path) -> Path:
        """메타데이터 JSON 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(metadata.to_json())

        return output_path

    def load(self, input_path: Path) -> VideoMetadata:
        """메타데이터 로드"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return VideoMetadata.from_dict(data)


def format_for_youtube(metadata: VideoMetadata) -> str:
    """YouTube 업로드용 포맷 출력"""
    output = []
    output.append("=" * 50)
    output.append("📺 YOUTUBE 메타데이터")
    output.append("=" * 50)
    output.append(f"\n📌 제목:\n{metadata.title}")
    output.append(f"\n📝 설명:\n{metadata.description}")
    output.append(f"\n🏷️ 태그:\n{', '.join(metadata.tags)}")
    output.append(f"\n#️⃣ 해시태그:\n{' '.join(metadata.hashtags)}")
    output.append("\n" + "=" * 50)
    return "\n".join(output)
