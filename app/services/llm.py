import json
import logging
import re
import requests
from typing import List, Optional, Dict

import g4f
from loguru import logger
from openai import AzureOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from app.models.exception import LLMError
from app.config import config
from app.services.youtube_trend import analyze_youtube_trends
from app.utils import cache, utils

_max_retries = 5


def _generate_response(prompt: str) -> str:
    try:
        content = ""
        
        # Check cache first
        cache_key = f"llm:{utils.md5(prompt)}"
        cached_content = cache.get_cache(cache_key)
        if cached_content:
            logger.info(f"LLM response found in cache for key: {cache_key}")
            return cached_content

        llm_provider = config.app.get("llm_provider", "openai").lower()
        logger.info(f"llm provider: {llm_provider}")
        if llm_provider == "g4f":
            model_name = config.app.get("g4f_model_name", "")
            if not model_name:
                model_name = "gpt-3.5-turbo-16k-0613"
            content = g4f.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
        else:
            api_version = ""  # for azure
            if llm_provider == "moonshot":
                api_key = config.app.get("moonshot_api_key")
                model_name = config.app.get("moonshot_model_name")
                base_url = "https://api.moonshot.cn/v1"
            elif llm_provider == "ollama":
                # api_key = config.app.get("openai_api_key")
                api_key = "ollama"  # any string works but you are required to have one
                model_name = config.app.get("ollama_model_name")
                base_url = config.app.get("ollama_base_url", "")
                if not base_url:
                    base_url = "http://localhost:11434/v1"
            elif llm_provider == "openai":
                api_key = config.app.get("openai_api_key")
                model_name = config.app.get("openai_model_name")
                base_url = config.app.get("openai_base_url", "")
                if not base_url:
                    base_url = "https://api.openai.com/v1"
            elif llm_provider == "oneapi":
                api_key = config.app.get("oneapi_api_key")
                model_name = config.app.get("oneapi_model_name")
                base_url = config.app.get("oneapi_base_url", "")
            elif llm_provider == "azure":
                api_key = config.app.get("azure_api_key")
                model_name = config.app.get("azure_model_name")
                base_url = config.app.get("azure_base_url", "")
                api_version = config.app.get("azure_api_version", "2024-02-15-preview")
            elif llm_provider == "gemini":
                api_key = config.app.get("gemini_api_key")
                model_name = config.app.get("gemini_model_name")
                base_url = "***"
            elif llm_provider == "qwen":
                api_key = config.app.get("qwen_api_key")
                model_name = config.app.get("qwen_model_name")
                base_url = "***"
            elif llm_provider == "cloudflare":
                api_key = config.app.get("cloudflare_api_key")
                model_name = config.app.get("cloudflare_model_name")
                account_id = config.app.get("cloudflare_account_id")
                base_url = "***"
            elif llm_provider == "deepseek":
                api_key = config.app.get("deepseek_api_key")
                model_name = config.app.get("deepseek_model_name")
                base_url = config.app.get("deepseek_base_url")
                if not base_url:
                    base_url = "https://api.deepseek.com"
            elif llm_provider == "ernie":
                api_key = config.app.get("ernie_api_key")
                secret_key = config.app.get("ernie_secret_key")
                base_url = config.app.get("ernie_base_url")
                model_name = "***"
                if not secret_key:
                    raise ValueError(
                        f"{llm_provider}: secret_key is not set, please set it in the config.toml file."
                    )
            elif llm_provider == "pollinations":
                try:
                    base_url = config.app.get("pollinations_base_url", "")
                    if not base_url:
                        base_url = "https://text.pollinations.ai/openai"
                    model_name = config.app.get("pollinations_model_name", "openai-fast")
                   
                    # Prepare the payload
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "seed": 101  # Optional but helps with reproducibility
                    }
                    
                    # Optional parameters if configured
                    if config.app.get("pollinations_private"):
                        payload["private"] = True
                    if config.app.get("pollinations_referrer"):
                        payload["referrer"] = config.app.get("pollinations_referrer")
                    
                    headers = {
                        "Content-Type": "application/json"
                    }
                    
                    # Make the API request
                    response = requests.post(base_url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    
                    if result and "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        raise LLMError(f"[{llm_provider}] returned an invalid response format")
                        
                except requests.exceptions.RequestException as e:
                    raise Exception(f"[{llm_provider}] request failed: {str(e)}")
                except Exception as e:
                    raise Exception(f"[{llm_provider}] error: {str(e)}")

            if llm_provider not in ["pollinations", "ollama"]:  # Skip validation for providers that don't require API key
                if not api_key:
                    raise LLMError(
                        f"{llm_provider}: api_key is not set, please set it in the config.toml file."
                    )
                if not model_name:
                    raise LLMError(
                        f"{llm_provider}: model_name is not set, please set it in the config.toml file."
                    )
                if not base_url:
                    raise LLMError(
                        f"{llm_provider}: base_url is not set, please set it in the config.toml file."
                    )

            if llm_provider == "qwen":
                import dashscope
                from dashscope.api_entities.dashscope_response import GenerationResponse

                dashscope.api_key = api_key
                response = dashscope.Generation.call(
                    model=model_name, messages=[{"role": "user", "content": prompt}]
                )
                if response:
                    if isinstance(response, GenerationResponse):
                        status_code = response.status_code
                        if status_code != 200:
                            raise LLMError(
                                f'[{llm_provider}] returned an error response: "{response}"'
                            )

                        content = response["output"]["text"]
                        return content
                    else:
                        raise LLMError(
                            f'[{llm_provider}] returned an invalid response: "{response}"'
                        )
                else:
                    raise LLMError(f"[{llm_provider}] returned an empty response")

            if llm_provider == "gemini":
                import google.generativeai as genai

                genai.configure(api_key=api_key, transport="rest")

                generation_config = {
                    "temperature": 0.5,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 2048,
                }

                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                ]

                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                )

                try:
                    response = model.generate_content(prompt)
                    candidates = response.candidates
                    generated_text = candidates[0].content.parts[0].text
                except (AttributeError, IndexError) as e:
                    logger.error(f"Gemini Error: {e}")

                return generated_text

            if llm_provider == "cloudflare":
                response = requests.post(
                    f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a friendly assistant",
                            },
                            {"role": "user", "content": prompt},
                        ]
                    },
                )
                result = response.json()
                logger.info(result)
                return result["result"]["response"]

            if llm_provider == "ernie":
                response = requests.post(
                    "https://aip.baidubce.com/oauth/2.0/token", 
                    params={
                        "grant_type": "client_credentials",
                        "client_id": api_key,
                        "client_secret": secret_key,
                    }
                )
                access_token = response.json().get("access_token")
                url = f"{base_url}?access_token={access_token}"

                payload = json.dumps(
                    {
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.5,
                        "top_p": 0.8,
                        "penalty_score": 1,
                        "disable_search": False,
                        "enable_citation": False,
                        "response_format": "text",
                    }
                )
                headers = {"Content-Type": "application/json"}

                response = requests.request(
                    "POST", url, headers=headers, data=payload
                ).json()
                return response.get("result")

            if llm_provider == "azure":
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=base_url,
                )
            else:
                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )

            response = client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": prompt}]
            )
            if response:
                if isinstance(response, ChatCompletion):
                    content = response.choices[0].message.content
            else:
                raise LLMError(
                    f"[{llm_provider}] returned an empty response, please check your network connection and try again."
                )

        # Save to cache
        if content:
            cache.set_cache(cache_key, content, ttl=3600 * 24) # Cache for 24 hours

        return content
    except Exception as e:
        logger.exception(f"Error generating response from LLM provider '{llm_provider}'. Prompt: '{prompt[:100]}...'")
        if isinstance(e, LLMError):
            raise e
        raise LLMError(f"An unexpected error occurred with LLM provider {llm_provider}: {e}") from e


def generate_script(
    video_subject: str, language: str = "", paragraph_number: int = 1
) -> str:
    prompt_template = f"""
# 역할: 비디오 스크립트 작가

## 목표:
주어진 영상 주제에 맞춰 스크립트를 생성합니다.

## Constrains:
1. the script is to be returned as a string with the specified number of paragraphs.
2. do not under any circumstance reference this prompt in your response.
3. get straight to the point, don't start with unnecessary things like, "welcome to this video".
4. you must not include any type of markdown or formatting in the script, never use a title.
5. only return the raw content of the script.
6. do not include "voiceover", "narrator" or similar indicators of what should be spoken at the beginning of each paragraph or line.
7. you must not mention the prompt, or anything about the script itself. also, never talk about the amount of paragraphs or lines. just write the script.
8. respond in the same language as the video subject.

# 초기 설정:
- 영상 주제: {video_subject}
- 단락 수: {paragraph_number}
"""
    prompt = prompt_template.strip()
    if language:
        prompt += f"\n- 응답 언어: {language}"

    final_script = ""
    logger.info(f"subject: {video_subject}")

    def format_response(response):
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        # selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        return "\n\n".join(paragraphs)

    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=prompt)
            if not response:
                raise LLMError("LLM returned an empty response.")
            
            final_script = format_response(response)

            # g4f may return an error message
            if final_script and "Daily quota exhausted" in final_script:
                raise ValueError(final_script)

            if final_script:
                break
        except LLMError as e:
            logger.warning(f"Attempt {i + 1}/{_max_retries} to generate script failed: {e}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred during script generation on attempt {i + 1}")

    logger.success(f"Script generation completed (length: {len(final_script)}).")
    return final_script.strip()


def generate_terms(video_subject: str, video_script: str, amount: int = 5) -> List[str]:
    prompt_template = f"""
# 역할: 영상 검색어 생성기

## 목표:
영상 주제에 맞는 스톡 비디오 검색어 {amount}개를 생성합니다.

## 제약 조건:
1. the search terms are to be returned as a json-array of strings.
2. each search term should consist of 1-3 words, always add the main subject of the video.
3. you must only return the json-array of strings. you must not return anything else. you must not return the script.
4. the search terms must be related to the subject of the video.
5. reply with english search terms only.

## 출력 예시:
["search term 1", "search term 2", "search term 3","search term 4","search term 5"]

## 컨텍스트:
### 영상 주제
{video_subject}

### 비디오 스크립트
{video_script}
"""
    prompt = prompt_template.strip()

    logger.info(f"subject: {video_subject}")

    search_terms = []
    response = ""
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt)
            if not response:
                raise LLMError("LLM returned an empty response for terms generation.")

            search_terms = json.loads(response)
            if not isinstance(search_terms, list) or not all(
                isinstance(term, str) for term in search_terms
            ):
                raise LLMError("LLM response is not a valid JSON array of strings.")

        except json.JSONDecodeError:
            if response:
                match = re.search(r"\[.*]", response)
                if match:
                    try:
                        search_terms = json.loads(match.group())
                    except json.JSONDecodeError:
                        raise LLMError(f"Failed to parse JSON from LLM response: {response}")

        if search_terms and isinstance(search_terms, list) and len(search_terms) > 0:
            break
        if i < _max_retries:
            logger.warning(f"Attempt {i + 1}/{_max_retries} to generate video terms failed. Response: '{response[:200]}...'")

    logger.success(f"completed: \n{search_terms}")
    return search_terms


def generate_viral_script(
    video_subject: str,
    language: str = "ko",
    paragraph_number: int = 1,
    use_trend_analysis: bool = True,
    region_code: str = "KR"
) -> Dict[str, any]:
    """
    유튜브 트렌드 분석을 활용한 바이럴 스크립트 생성

    Args:
        video_subject: 영상 주제
        language: 언어 코드
        paragraph_number: 단락 수
        use_trend_analysis: 트렌드 분석 사용 여부
        region_code: 국가 코드

    Returns:
        스크립트 및 메타데이터가 포함된 딕셔너리
    """
    result = {
        "script": "",
        "viral_keywords": [],
        "title_suggestions": [],
        "hooks": [],
        "metadata": {}
    }

    # 트렌드 분석 수행
    trend_data = None
    if use_trend_analysis:
        try:
            youtube_api_key = config.app.get("youtube_api_key", "")
            trend_data = analyze_youtube_trends(
                topic=video_subject,
                api_key=youtube_api_key if youtube_api_key else None,
                region_code=region_code
            )
            logger.info(f"Trend analysis completed for: {video_subject}")
        except Exception as e:
            logger.warning(f"Trend analysis failed, using standard generation: {e}")
            trend_data = None

    # 트렌드 데이터를 활용한 프롬프트 개선
    if trend_data:
        viral_keywords = trend_data.get("viral_keywords", [])
        hooks = trend_data.get("content_hooks", [])

        # 바이럴 키워드를 포함한 개선된 프롬프트
        viral_keywords_str = ", ".join(viral_keywords[:5]) if viral_keywords else ""
        hook = hooks[0] if hooks else ""

        enhanced_prompt = f"""
# Role: Viral Video Script Generator

## Goals:
Generate a highly engaging, viral-worthy script for a video about "{video_subject}".

## Viral Strategy:
- Incorporate these trending keywords naturally: {viral_keywords_str}
- Start with an attention-grabbing hook: "{hook}"
- Use storytelling techniques that create curiosity and emotional engagement
- Include surprising facts or unique perspectives
- End with a strong call-to-action or memorable conclusion

## Constraints:
1. Return the script as a string with {paragraph_number} paragraphs
2. Do not reference this prompt in your response
3. Get straight to the point with a powerful opening
4. No markdown or formatting - raw script content only
5. Do not include "voiceover", "narrator" or similar indicators
6. Never mention the prompt itself or script structure
7. Respond in {language} language

## Style Guidelines:
- Use conversational, energetic tone
- Include moments of surprise or revelation
- Create curiosity gaps that keep viewers watching
- Use specific examples and vivid descriptions

# Video Subject: {video_subject}
# Paragraphs: {paragraph_number}
""".strip()
    else:
        # 기본 프롬프트
        enhanced_prompt = f"""
# Role: Video Script Generator

## Goals:
Generate an engaging script for a video about "{video_subject}".

## Constraints:
1. Return the script with {paragraph_number} paragraphs
2. Do not reference this prompt
3. Get straight to the point
4. No markdown or formatting
5. Raw content only
6. Respond in {language} language

# Video Subject: {video_subject}
# Paragraphs: {paragraph_number}
""".strip()

    # 스크립트 생성
    final_script = ""
    for i in range(_max_retries):
        try:
            response = _generate_response(prompt=enhanced_prompt)
            if response:
                # Clean the script
                response = response.replace("*", "").replace("#", "")
                response = re.sub(r"\[.*\]", "", response)
                response = re.sub(r"\(.*\)", "", response)
                final_script = response.strip()

            if final_script and "Daily quota exhausted" not in final_script:
                break

        except Exception as e:
            logger.error(f"Failed to generate viral script: {e}")

        if i < _max_retries - 1:
            logger.warning(f"Retrying script generation... {i + 1}/{_max_retries}")

    # 결과 구성
    result["script"] = final_script

    if trend_data:
        result["viral_keywords"] = trend_data.get("viral_keywords", [])
        result["title_suggestions"] = trend_data.get("title_suggestions", [])
        result["hooks"] = trend_data.get("content_hooks", [])
        result["recommended_duration"] = trend_data.get("recommended_duration_seconds", 90)
        result["metadata"] = trend_data.get("metadata", {})

    if final_script:
        logger.success(f"Viral script generated successfully")
    else:
        logger.error("Failed to generate viral script")

    return result


if __name__ == "__main__":
    video_subject = "What is the meaning of life"
    # 한국어 스크립트 생성을 위해 language를 'ko'로 변경
    script = generate_script(video_subject=video_subject, language="ko", paragraph_number=1)
    logger.info(f"Generated Script: {script}")
    search_terms = generate_terms(
        video_subject=video_subject, video_script=script, amount=5
    )
    