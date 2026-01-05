"""
재검토 루프 모듈
생성된 스크립트를 평가하고 개선
Google Gemini API 사용
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import re
import yaml

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False

from .script_generator import Script


@dataclass
class ReviewResult:
    """리뷰 결과 데이터 클래스"""
    hook_score: float
    accuracy_score: float
    clarity_score: float
    example_score: float
    cta_score: float
    flow_score: float
    tone_score: float
    average: float
    feedback: str
    passed: bool
    improved_script: Optional[Script] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'hook_score': self.hook_score,
            'accuracy_score': self.accuracy_score,
            'clarity_score': self.clarity_score,
            'example_score': self.example_score,
            'cta_score': self.cta_score,
            'flow_score': self.flow_score,
            'tone_score': self.tone_score,
            'average': self.average,
            'feedback': self.feedback,
            'passed': self.passed
        }


class ReviewLoop:
    """스크립트 재검토 및 개선 루프 (Google Gemini API)"""

    MIN_SCORE = 8.0
    MAX_ITERATIONS = 3

    def __init__(
        self,
        api_key: str,
        prompts_path: str | Path,
        min_score: float = 8.0,
        max_iterations: int = 3
    ):
        """
        Args:
            api_key: Google API 키
            prompts_path: prompts.yaml 파일 경로
            min_score: 통과 최소 점수
            max_iterations: 최대 반복 횟수
        """
        if not HAS_GENAI:
            raise ImportError("google-generativeai 패키지가 설치되지 않았습니다. pip install google-generativeai")

        genai.configure(api_key=api_key)
        # gemini-3-flash-preview: 더 높은 무료 쿼터 + 안정적
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        self.prompts_path = Path(prompts_path)
        self.prompts = self._load_prompts()
        self.MIN_SCORE = min_score
        self.MAX_ITERATIONS = max_iterations

    def _load_prompts(self) -> dict:
        """프롬프트 템플릿 로드"""
        if not self.prompts_path.exists():
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompts_path}")

        with open(self.prompts_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def review_and_improve(
        self,
        script: Script,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3
    ) -> Script:
        """
        스크립트 검토 및 개선

        Args:
            script: 검토할 Script 객체
            model: Claude 모델명
            temperature: 생성 온도

        Returns:
            개선된 Script 객체 (또는 통과한 원본)
        """
        current_script = script

        for iteration in range(self.MAX_ITERATIONS):
            result = self._evaluate(current_script, model, temperature)
            current_script.review_score = result.average

            if result.passed:
                return current_script

            if iteration < self.MAX_ITERATIONS - 1:
                # 개선 시도
                improved = self._improve(current_script, result.feedback, model, temperature)
                if improved:
                    current_script = improved

        return current_script

    def _evaluate(
        self,
        script: Script,
        model: str,
        temperature: float
    ) -> ReviewResult:
        """
        스크립트 평가

        Args:
            script: 평가할 Script 객체
            model: Gemini 모델명 (미사용, 호환성 유지)
            temperature: 생성 온도

        Returns:
            ReviewResult 객체
        """
        system_prompt = self.prompts['review_loop']['system']
        user_template = self.prompts['review_loop']['user_template']

        user_prompt = user_template.format(script=script.full_text)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1500,
                    temperature=temperature
                )
            )

            response_text = response.text
            return self._parse_evaluation(response_text)

        except Exception as e:
            # API 오류 시 기본값 반환
            return ReviewResult(
                hook_score=7.0,
                accuracy_score=8.0,
                clarity_score=7.0,
                example_score=7.0,
                cta_score=7.0,
                flow_score=7.0,
                tone_score=7.0,
                average=7.14,
                feedback=f"평가 실패: {str(e)}",
                passed=False
            )

    def _parse_evaluation(self, response: str) -> ReviewResult:
        """
        평가 응답 파싱

        Args:
            response: Claude API 응답

        Returns:
            ReviewResult 객체
        """
        # 점수 추출 정규식
        scores = {
            'hook': 7.0,
            'accuracy': 8.0,
            'clarity': 7.0,
            'example': 7.0,
            'cta': 7.0,
            'flow': 7.0,
            'tone': 7.0
        }

        # 각 항목 점수 추출
        hook_match = re.search(r'훅 강도[:\s]*(\d+(?:\.\d+)?)/10', response)
        accuracy_match = re.search(r'명언 정확성[:\s]*(\d+(?:\.\d+)?)/10', response)
        clarity_match = re.search(r'해설 명확성[:\s]*(\d+(?:\.\d+)?)/10', response)
        example_match = re.search(r'예시 구체성[:\s]*(\d+(?:\.\d+)?)/10', response)
        cta_match = re.search(r'CTA 효과[:\s]*(\d+(?:\.\d+)?)/10', response)
        flow_match = re.search(r'전체 흐름[:\s]*(\d+(?:\.\d+)?)/10', response)
        tone_match = re.search(r'톤 적절성[:\s]*(\d+(?:\.\d+)?)/10', response)

        if hook_match:
            scores['hook'] = float(hook_match.group(1))
        if accuracy_match:
            scores['accuracy'] = float(accuracy_match.group(1))
        if clarity_match:
            scores['clarity'] = float(clarity_match.group(1))
        if example_match:
            scores['example'] = float(example_match.group(1))
        if cta_match:
            scores['cta'] = float(cta_match.group(1))
        if flow_match:
            scores['flow'] = float(flow_match.group(1))
        if tone_match:
            scores['tone'] = float(tone_match.group(1))

        # 평균 점수 계산
        average = sum(scores.values()) / len(scores)

        # 평균 점수 추출 (응답에 있는 경우)
        avg_match = re.search(r'평균 점수[:\s]*(\d+(?:\.\d+)?)/10', response)
        if avg_match:
            average = float(avg_match.group(1))

        # 개선 필요 여부
        needs_improvement = '예' in response.split('개선 필요 여부')[1][:10] if '개선 필요 여부' in response else average < self.MIN_SCORE

        # 피드백 추출
        feedback = ""
        feedback_match = re.search(r'개선 방안[^#]*?(?=##|$)', response, re.DOTALL)
        if feedback_match:
            feedback = feedback_match.group(0).strip()

        return ReviewResult(
            hook_score=scores['hook'],
            accuracy_score=scores['accuracy'],
            clarity_score=scores['clarity'],
            example_score=scores['example'],
            cta_score=scores['cta'],
            flow_score=scores['flow'],
            tone_score=scores['tone'],
            average=round(average, 2),
            feedback=feedback,
            passed=not needs_improvement and average >= self.MIN_SCORE
        )

    def _improve(
        self,
        script: Script,
        feedback: str,
        model: str,
        temperature: float
    ) -> Optional[Script]:
        """
        피드백 기반 스크립트 개선

        Args:
            script: 개선할 Script 객체
            feedback: 개선 피드백
            model: Gemini 모델명 (미사용, 호환성 유지)
            temperature: 생성 온도

        Returns:
            개선된 Script 객체 또는 None
        """
        improvement_prompt = f"""다음 스크립트를 개선해주세요.

## 원본 스크립트
{script.full_text}

## 개선 피드백
{feedback}

## 개선 요청
위 피드백을 반영하여 스크립트를 개선해주세요.
기존 형식([훅], [명언], [해설], [예시], [CTA])을 유지해주세요.
"""

        try:
            response = self.model.generate_content(
                improvement_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=temperature
                )
            )

            response_text = response.text

            # 개선된 스크립트 파싱
            return self._parse_improved_script(response_text, script)

        except Exception:
            return None

    def _parse_improved_script(self, response: str, original: Script) -> Optional[Script]:
        """
        개선된 스크립트 파싱

        Args:
            response: 개선된 스크립트 텍스트
            original: 원본 Script 객체

        Returns:
            파싱된 Script 객체 또는 None
        """
        # 섹션 추출
        hook_match = re.search(r'\[훅\]\s*\n(.+?)(?=\n\[명언\])', response, re.DOTALL)
        quote_match = re.search(r'\[명언\]\s*\n(.+?)(?=\n\[해설\])', response, re.DOTALL)
        explanation_match = re.search(r'\[해설\]\s*\n(.+?)(?=\n\[예시\])', response, re.DOTALL)
        example_match = re.search(r'\[예시\]\s*\n(.+?)(?=\n\[CTA\])', response, re.DOTALL)
        cta_match = re.search(r'\[CTA\]\s*\n(.+?)$', response, re.DOTALL)

        if not all([hook_match, quote_match, explanation_match, example_match, cta_match]):
            return None

        hook = hook_match.group(1).strip()
        quote_text = quote_match.group(1).strip()
        explanation = explanation_match.group(1).strip()
        example = example_match.group(1).strip()
        cta = cta_match.group(1).strip()

        full_text = f"""[훅]
{hook}

[명언]
{quote_text}

[해설]
{explanation}

[예시]
{example}

[CTA]
{cta}"""

        import uuid
        return Script(
            id=str(uuid.uuid4()),
            quote_id=original.quote_id,
            hook=hook,
            quote_text=quote_text,
            explanation=explanation,
            example=example,
            cta=cta,
            full_text=full_text,
            hook_type=original.hook_type,
            cta_type=original.cta_type,
            author=original.author,
            source=original.source,
            themes=original.themes,
            review_score=original.review_score
        )

    def evaluate_only(
        self,
        script: Script,
        model: str = "gemini-2.5-flash"
    ) -> ReviewResult:
        """
        스크립트 평가만 수행 (개선 없이)

        Args:
            script: 평가할 Script 객체
            model: Claude 모델명

        Returns:
            ReviewResult 객체
        """
        return self._evaluate(script, model, 0.3)


class SimpleReviewLoop:
    """API 없이 간단한 규칙 기반 검토 (테스트/백업용)"""

    MIN_SCORE = 8.0

    def review_and_improve(self, script: Script) -> Script:
        """간단한 규칙 기반 검토"""
        score = 8.0

        # 훅 길이 체크
        if len(script.hook) < 10:
            score -= 1.0
        elif len(script.hook) > 50:
            score -= 0.5

        # 해설 길이 체크
        if len(script.explanation) < 50:
            score -= 1.0

        # CTA 존재 체크
        if len(script.cta) < 10:
            score -= 1.0

        script.review_score = score
        return script


if __name__ == '__main__':
    # 간단 테스트
    print("ReviewLoop 모듈 로드 완료")
    print(f"기본 최소 점수: {ReviewLoop.MIN_SCORE}")
    print(f"최대 반복 횟수: {ReviewLoop.MAX_ITERATIONS}")
