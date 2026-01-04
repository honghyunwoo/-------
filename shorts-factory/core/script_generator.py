"""
스크립트 생성 모듈
Claude API를 사용하여 명언 기반 쇼츠 스크립트 생성
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from pathlib import Path
import uuid
import yaml
import re

try:
    import anthropic
except ImportError:
    anthropic = None

from .quote_loader import Quote


HookType = Literal["H1", "H2", "H3", "H4", "H5"]
CTAType = Literal["C1", "C2", "C3", "C4", "C5"]

HOOK_DESCRIPTIONS = {
    "H1": "질문형 - 시청자에게 직접 질문",
    "H2": "충격형 - 놀라운 사실로 시선 끌기",
    "H3": "공감형 - 시청자의 감정에 공감",
    "H4": "비밀형 - 숨겨진 지혜 공개",
    "H5": "대비형 - 대조를 통한 흥미 유발"
}

CTA_DESCRIPTIONS = {
    "C1": "저장 유도 - 영상 저장 유도",
    "C2": "팔로우 유도 - 채널 구독 유도",
    "C3": "오픈 엔딩 - 질문으로 재시청 유도",
    "C4": "공유 유도 - 영상 공유 유도",
    "C5": "시리즈 예고 - 다음 영상 예고"
}


@dataclass
class Script:
    """스크립트 데이터 클래스"""
    id: str
    quote_id: int
    hook: str
    quote_text: str
    explanation: str
    example: str
    cta: str
    full_text: str
    hook_type: HookType
    cta_type: CTAType
    author: str = ""
    source: str = ""
    themes: list = field(default_factory=list)
    review_score: float = 0.0

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'hook': self.hook,
            'quote_text': self.quote_text,
            'explanation': self.explanation,
            'example': self.example,
            'cta': self.cta,
            'full_text': self.full_text,
            'hook_type': self.hook_type,
            'cta_type': self.cta_type,
            'author': self.author,
            'source': self.source,
            'themes': self.themes,
            'review_score': self.review_score
        }

    def get_tts_text(self) -> str:
        """TTS용 텍스트 반환 (섹션 마커 제거)"""
        text = self.full_text
        # 섹션 마커 제거
        text = re.sub(r'\[훅\]|\[명언\]|\[해설\]|\[예시\]|\[CTA\]', '', text)
        # 여러 줄바꿈을 하나로
        text = re.sub(r'\n+', '\n', text)
        return text.strip()


class ScriptGenerationError(Exception):
    """스크립트 생성 실패 예외"""
    pass


class ScriptGenerator:
    """Claude API를 사용한 스크립트 생성기"""

    def __init__(self, api_key: str, prompts_path: str | Path):
        """
        Args:
            api_key: Anthropic API 키
            prompts_path: prompts.yaml 파일 경로
        """
        if anthropic is None:
            raise ImportError("anthropic 패키지가 설치되지 않았습니다. pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompts_path = Path(prompts_path)
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> dict:
        """프롬프트 템플릿 로드"""
        if not self.prompts_path.exists():
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompts_path}")

        with open(self.prompts_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate(
        self,
        quote: Quote,
        hook_type: HookType = "H1",
        cta_type: CTAType = "C3",
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Script:
        """
        스크립트 생성

        Args:
            quote: Quote 객체
            hook_type: 훅 유형 (H1-H5)
            cta_type: CTA 유형 (C1-C5)
            model: Claude 모델명
            temperature: 생성 온도
            max_tokens: 최대 토큰 수

        Returns:
            Script 객체
        """
        # 프롬프트 구성
        system_prompt = self.prompts['script_generator']['system']
        user_template = self.prompts['script_generator']['user_template']

        user_prompt = user_template.format(
            quote_text=quote.text,
            author=quote.author,
            source=quote.source,
            themes=', '.join(quote.themes),
            hook_type=hook_type,
            hook_description=HOOK_DESCRIPTIONS[hook_type],
            cta_type=cta_type,
            cta_description=CTA_DESCRIPTIONS[cta_type]
        )

        try:
            # Claude API 호출
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = message.content[0].text
            return self._parse_response(response_text, quote, hook_type, cta_type)

        except Exception as e:
            raise ScriptGenerationError(f"스크립트 생성 실패: {e}")

    def _parse_response(
        self,
        response: str,
        quote: Quote,
        hook_type: HookType,
        cta_type: CTAType
    ) -> Script:
        """
        API 응답 파싱

        Args:
            response: Claude API 응답 텍스트
            quote: 원본 Quote 객체
            hook_type: 훅 유형
            cta_type: CTA 유형

        Returns:
            파싱된 Script 객체
        """
        # 섹션별 추출
        sections = {
            'hook': '',
            'quote': '',
            'explanation': '',
            'example': '',
            'cta': ''
        }

        # 정규식으로 섹션 추출
        hook_match = re.search(r'\[훅\]\s*\n(.+?)(?=\n\[명언\]|\n\[해설\]|$)', response, re.DOTALL)
        quote_match = re.search(r'\[명언\]\s*\n(.+?)(?=\n\[해설\]|\n\[예시\]|$)', response, re.DOTALL)
        explanation_match = re.search(r'\[해설\]\s*\n(.+?)(?=\n\[예시\]|\n\[CTA\]|$)', response, re.DOTALL)
        example_match = re.search(r'\[예시\]\s*\n(.+?)(?=\n\[CTA\]|$)', response, re.DOTALL)
        cta_match = re.search(r'\[CTA\]\s*\n(.+?)$', response, re.DOTALL)

        if hook_match:
            sections['hook'] = hook_match.group(1).strip()
        if quote_match:
            sections['quote'] = quote_match.group(1).strip()
        if explanation_match:
            sections['explanation'] = explanation_match.group(1).strip()
        if example_match:
            sections['example'] = example_match.group(1).strip()
        if cta_match:
            sections['cta'] = cta_match.group(1).strip()

        # 전체 텍스트 조합
        full_text = f"""[훅]
{sections['hook']}

[명언]
{sections['quote']}

[해설]
{sections['explanation']}

[예시]
{sections['example']}

[CTA]
{sections['cta']}"""

        return Script(
            id=str(uuid.uuid4()),
            quote_id=quote.id,
            hook=sections['hook'],
            quote_text=sections['quote'],
            explanation=sections['explanation'],
            example=sections['example'],
            cta=sections['cta'],
            full_text=full_text,
            hook_type=hook_type,
            cta_type=cta_type,
            author=quote.author,
            source=quote.source,
            themes=quote.themes
        )

    def generate_simple(
        self,
        quote: Quote,
        hook_type: HookType = "H1",
        cta_type: CTAType = "C3"
    ) -> Script:
        """
        API 없이 템플릿 기반 간단 스크립트 생성 (테스트/백업용)

        Args:
            quote: Quote 객체
            hook_type: 훅 유형
            cta_type: CTA 유형

        Returns:
            Script 객체
        """
        # 기본 훅 템플릿
        hooks = {
            "H1": f"왜 우리는 매일 같은 걱정을 반복할까요?",
            "H2": f"2000년 전 {quote.author}가 한 이 말이 당신을 바꿉니다.",
            "H3": f"마음이 지쳐있다면, 이 영상을 끝까지 보세요.",
            "H4": f"상위 1%만 아는 마음 관리의 비밀.",
            "H5": f"대부분은 걱정하지만, 현명한 사람은 준비합니다."
        }

        # 기본 CTA 템플릿
        ctas = {
            "C1": "이 영상을 저장해두고, 힘들 때마다 꺼내보세요.",
            "C2": "매일 스토아의 지혜를 받아보세요.",
            "C3": "당신은 오늘 어떤 선택을 하시겠습니까?",
            "C4": "이 지혜가 필요한 사람에게 공유해주세요.",
            "C5": "더 깊은 이야기는 다음 영상에서."
        }

        hook = hooks.get(hook_type, hooks["H1"])
        cta = ctas.get(cta_type, ctas["C3"])

        explanation = f"{quote.author}는 {quote.source}에서 이렇게 말했습니다. 이 지혜는 2000년이 지난 지금도 우리에게 깊은 울림을 줍니다."
        example = "오늘 하루, 이 말을 마음에 새기고 실천해보세요."

        full_text = f"""[훅]
{hook}

[명언]
"{quote.text}" - {quote.author}

[해설]
{explanation}

[예시]
{example}

[CTA]
{cta}"""

        return Script(
            id=str(uuid.uuid4()),
            quote_id=quote.id,
            hook=hook,
            quote_text=f'"{quote.text}" - {quote.author}',
            explanation=explanation,
            example=example,
            cta=cta,
            full_text=full_text,
            hook_type=hook_type,
            cta_type=cta_type,
            author=quote.author,
            source=quote.source,
            themes=quote.themes
        )


if __name__ == '__main__':
    # 테스트 (API 키 없이 간단 생성)
    from quote_loader import QuoteLoader

    loader = QuoteLoader('templates/stoic/quotes_library.json')
    quote = loader.get_by_id(1)

    # 간단 생성 테스트
    class MockGenerator:
        def generate_simple(self, quote, hook_type="H1", cta_type="C3"):
            return ScriptGenerator.__dict__['generate_simple'](self, quote, hook_type, cta_type)

    # 실제 테스트는 API 키 필요
    print(f"명언: {quote.text}")
    print(f"저자: {quote.author}")
