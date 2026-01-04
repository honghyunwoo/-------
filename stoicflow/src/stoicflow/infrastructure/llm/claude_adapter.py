"""Claude (Anthropic) LLM adapter implementation."""

import json
from datetime import datetime

from loguru import logger

from stoicflow.application.interfaces.llm_provider import LLMProvider
from stoicflow.config.settings import settings
from stoicflow.domain.entities.script import Script

SCRIPT_GENERATION_PROMPT = """당신은 스토아 철학 전문가이자 유튜브 쇼츠 스크립트 작가입니다.

요청에 따라 60초 이내의 스토아 철학 동기부여 쇼츠 스크립트를 작성하세요.

## 형식 (반드시 JSON으로 응답)
{{
    "quote": "원문 명언 (한국어)",
    "author": "철학자 이름",
    "script": {{
        "hook": "주목을 끄는 질문 또는 상황 (2-3초, 15자 이내)",
        "quote_read": "명언을 자연스럽게 읽기 (8-12초)",
        "explanation": "현대적 해석과 적용 방법 (20-30초)",
        "cta": "시청자 참여 유도 질문 (3-5초, 20자 이내)"
    }},
    "tts_text": "전체 스크립트 (줄바꿈으로 구분)"
}}

## 스타일 가이드
- 일상 대화체로 작성 (친근하게)
- 구체적인 상황과 예시 사용
- 시청자가 즉시 적용할 수 있는 팁 제공
- 지나친 설교조 피하기

{context}
"""


class ClaudeAdapter(LLMProvider):
    """Claude API를 사용하는 LLM 어댑터."""

    def __init__(self):
        from anthropic import Anthropic

        api_key = settings.anthropic_api_key
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        self.client = Anthropic(api_key=api_key.get_secret_value())
        self.model = "claude-sonnet-4-20250514"  # 2026년 기준 최신 모델

    async def generate_script(
        self,
        topic: str | None = None,
        quote: str | None = None,
        author: str | None = None,
        style: str = "stoic",
    ) -> Script:
        """Claude를 사용하여 스크립트 생성."""
        context_parts = []
        if topic:
            context_parts.append(f"주제: {topic}")
        if quote:
            context_parts.append(f"사용할 명언: {quote}")
        if author:
            context_parts.append(f"철학자: {author}")

        context = "\n".join(context_parts) if context_parts else "자유 주제"

        prompt = SCRIPT_GENERATION_PROMPT.format(context=context)

        logger.debug(f"Generating script with Claude: {context}")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        content = response.content[0].text

        # Extract JSON from response
        try:
            # Try to find JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            data = json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

        # Create Script entity
        script_data = data.get("script", {})
        return Script(
            id=int(datetime.now().timestamp()),
            quote=data["quote"],
            author=data["author"],
            theme=style,
            hook=script_data["hook"],
            quote_read=script_data["quote_read"],
            explanation=script_data["explanation"],
            cta=script_data["cta"],
            tts_text=data.get("tts_text", ""),
        )

    async def improve_script(self, script: Script, feedback: str) -> Script:
        """피드백을 반영하여 스크립트 개선."""
        prompt = f"""현재 스크립트를 개선해주세요.

현재 스크립트:
- Hook: {script.hook}
- Quote: {script.quote_read}
- Explanation: {script.explanation}
- CTA: {script.cta}

피드백: {feedback}

개선된 스크립트를 JSON 형식으로 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        data = json.loads(content)
        script_data = data.get("script", data)

        return Script(
            id=script.id,
            quote=script.quote,
            author=script.author,
            theme=script.theme,
            hook=script_data.get("hook", script.hook),
            quote_read=script_data.get("quote_read", script.quote_read),
            explanation=script_data.get("explanation", script.explanation),
            cta=script_data.get("cta", script.cta),
            tts_text=data.get("tts_text", script.tts_text),
        )

    async def generate_title(self, script: Script) -> str:
        """유튜브 제목 생성."""
        prompt = f"""다음 스토아 철학 쇼츠의 유튜브 제목을 생성하세요.

명언: {script.quote}
철학자: {script.author}

요구사항:
- 50자 이내
- 호기심 유발
- 이모지 1-2개 사용 가능
- 클릭을 유도하되 어그로성 제목은 피할 것

제목만 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip().strip('"')

    async def generate_description(self, script: Script) -> str:
        """유튜브 설명 생성."""
        prompt = f"""다음 스토아 철학 쇼츠의 유튜브 설명을 생성하세요.

명언: {script.quote}
철학자: {script.author}
스크립트 요약: {script.explanation[:100]}...

요구사항:
- 200자 이내
- 명언의 핵심 메시지 포함
- 관련 해시태그 3-5개 포함
- 구독 유도 문구 자연스럽게 포함

설명만 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()

    async def generate_tags(self, script: Script) -> list[str]:
        """유튜브 태그 생성."""
        prompt = f"""다음 스토아 철학 쇼츠의 유튜브 태그를 생성하세요.

명언: {script.quote}
철학자: {script.author}

요구사항:
- 10-15개 태그
- 쉼표로 구분
- 한국어 태그 위주, 영어 2-3개 포함

태그만 쉼표로 구분하여 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        tags_str = response.content[0].text.strip()
        return [tag.strip() for tag in tags_str.split(",")]
