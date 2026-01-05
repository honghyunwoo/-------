"""
스크립트 생성 모듈
Google Gemini API를 사용하여 명언 기반 쇼츠 스크립트 생성
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from pathlib import Path
import uuid
import yaml
import re

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

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
    """Google Gemini API를 사용한 스크립트 생성기"""

    def __init__(self, api_key: str, prompts_path: str | Path):
        """
        Args:
            api_key: Google API 키
            prompts_path: prompts.yaml 파일 경로
        """
        if not HAS_GENAI:
            raise ImportError("google-generativeai 패키지가 설치되지 않았습니다. pip install google-generativeai")

        genai.configure(api_key=api_key)
        # gemini-3-flash-preview: 더 높은 무료 쿼터 + 안정적
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
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
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 2000  # 충분한 토큰 확보
    ) -> Script:
        """
        스크립트 생성

        Args:
            quote: Quote 객체
            hook_type: 훅 유형 (H1-H5)
            cta_type: CTA 유형 (C1-C5)
            model: Gemini 모델명 (미사용, 호환성 유지)
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
            # Google Gemini API 호출
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )

            response_text = response.text

            # 디버깅: 원본 응답 저장
            debug_path = Path(__file__).parent.parent / 'output' / 'last_gemini_response.txt'
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Quote: {quote.text[:50]}... ===\n\n")
                f.write(response_text)

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

        # === 전처리: 다양한 형식 정규화 ===
        # 1. 마크다운 볼드 제거: **[훅]** → [훅]
        response = re.sub(r'\*+\s*\[', '[', response)
        response = re.sub(r'\]\s*\*+', ']', response)

        # 2. 불완전한 섹션 마커 수정: [해설 → [해설], [훅 → [훅] 등
        response = re.sub(r'\[(훅|명언|해설|예시|CTA)(?!\])', r'[\1]', response)

        # 3. 중복 섹션 마커 제거 (첫 번째만 유지)
        for marker in ['훅', '명언', '해설', '예시', 'CTA']:
            pattern = rf'(\[{marker}\]).*?(\[{marker}\])'
            response = re.sub(pattern, r'\1', response, flags=re.DOTALL)

        # 4. 연속 섹션 마커 사이의 빈 내용 제거하지 않음 (그대로 유지)

        # 5. 괄호 안 설명 제거: (패턴 인터럽트 + 호기심 자극) 등
        response = re.sub(r'\n\s*\([^)]+\)\s*\n', '\n', response)

        # === 섹션 추출 ===
        # 순서대로 섹션 경계 찾기
        markers = [
            (r'\[훅\]', 'hook'),
            (r'\[명언\]', 'quote'),
            (r'\[해설\]', 'explanation'),
            (r'\[예시\]', 'example'),
            (r'\[CTA\]', 'cta')
        ]

        # 각 섹션의 시작 위치 찾기
        positions = []
        for pattern, name in markers:
            match = re.search(pattern, response)
            if match:
                positions.append((match.start(), match.end(), name))

        # 위치순으로 정렬
        positions.sort(key=lambda x: x[0])

        # 각 섹션 내용 추출
        for i, (start, end, name) in enumerate(positions):
            # 다음 섹션 시작 위치 또는 문서 끝
            next_start = positions[i + 1][0] if i + 1 < len(positions) else len(response)
            content = response[end:next_start].strip()
            # 앞뒤 공백과 불필요한 마커 제거
            content = re.sub(r'^\s*[\n\r]+', '', content)
            content = re.sub(r'[\n\r]+\s*$', '', content)
            sections[name] = content

        # 하위호환: 기존 정규식도 백업으로 시도
        if not sections['hook']:
            hook_match = re.search(r'\[훅\][\s\n]*(.+?)(?=\[명언\]|\[해설\]|$)', response, re.DOTALL)
            if hook_match:
                sections['hook'] = hook_match.group(1).strip()
        if not sections['quote']:
            quote_match = re.search(r'\[명언\][\s\n]*(.+?)(?=\[해설\]|\[예시\]|$)', response, re.DOTALL)
            if quote_match:
                sections['quote'] = quote_match.group(1).strip()
        if not sections['explanation']:
            explanation_match = re.search(r'\[해설\][\s\n]*(.+?)(?=\[예시\]|\[CTA\]|$)', response, re.DOTALL)
            if explanation_match:
                sections['explanation'] = explanation_match.group(1).strip()
        if not sections['example']:
            example_match = re.search(r'\[예시\][\s\n]*(.+?)(?=\[CTA\]|$)', response, re.DOTALL)
            if example_match:
                sections['example'] = example_match.group(1).strip()
        if not sections['cta']:
            cta_match = re.search(r'\[CTA\][\s\n]*(.+?)$', response, re.DOTALL)
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
