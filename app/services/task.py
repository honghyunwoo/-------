"""
Core task execution service for video generation.

This module orchestrates the entire video generation pipeline, from script generation
to final video rendering, using asynchronous processing to improve performance.
"""
import math
import os.path
import asyncio
import re
from os import path
from typing import List, Optional, Tuple, Dict, Any

from loguru import logger
from sqlalchemy.orm import Session

from app.config import config
from app.models import const
from app.models.schema import (
    VideoConcatMode,
    VideoParams,
    TemplateCreate,
    Template,
    MaterialInfo,
)
from app.models.user import User
from app.services import (
    llm,
    material,
    subtitle,
    video,
    voice,
    template,
    youtube_uploader,
    history,
    auth,
    usage,
)
from app.services import state as sm
from app.utils import utils


def get_korean_voice_name(params: VideoParams) -> str:
    """
    한국어 음성 이름을 강제로 반환합니다.
    Phase 1 Task 2: 한국어 음성 실제 적용 검증
    """
    # 한국어 콘텐츠인 경우 한국어 음성 강제 적용
    if params.video_language == "ko" or "한국" in str(params.video_subject):
        korean_voice = "ko-KR-SunHiNeural"
        logger.info(f"🇰🇷 Korean content detected, using Korean voice: {korean_voice}")
        return korean_voice
    
    # 기본값도 한국어 음성으로 설정
    default_korean_voice = "ko-KR-SunHiNeural"
    logger.info(f"🎤 Using default Korean voice: {default_korean_voice}")
    return default_korean_voice


async def generate_script(task_id: str, params: VideoParams) -> Optional[str]:
    """
    Generates a video script using the LLM service.

    If a script is provided in the parameters, it's used directly. Otherwise,
    a new script is generated based on the video subject.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.

    Returns:
        Optional[str]: The generated video script, or None if generation fails.
    """
    logger.info("[Step 1/5] Generating video script...")
    video_script = params.video_script.strip()
    if not video_script:
        video_script = await asyncio.to_thread(
            llm.generate_script,
            video_subject=params.video_subject,
            language=params.video_language,
            paragraph_number=params.paragraph_number,
        )
    else:
        logger.debug(f"Using provided video script (length: {len(video_script)}).")

    if not video_script:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error(f"Task {task_id}: Failed to generate video script for subject: '{params.video_subject}'.")
        return None

    return video_script


async def generate_terms(
    task_id: str, params: VideoParams, video_script: str
) -> Optional[List[str]]:
    """
    Generates search terms for video materials using the LLM service.

    If terms are provided in the parameters, they are used directly. Otherwise,
    new terms are generated based on the video subject and script.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.
        video_script (str): The video script to base the terms on.

    Returns:
        Optional[List[str]]: A list of search terms, or None if generation fails.
    """
    logger.info("Generating video terms...")
    video_terms = params.video_terms
    if not video_terms:
        video_terms = await asyncio.to_thread(
            llm.generate_terms,
            video_subject=params.video_subject,
            video_script=video_script,
            amount=5,
        )
    else:
        if isinstance(video_terms, str):
            video_terms = [term.strip() for term in re.split(r"[,，]", video_terms)]
        elif isinstance(video_terms, list):
            video_terms = [term.strip() for term in video_terms]
        else:
            raise ValueError("video_terms must be a string or a list of strings.")

        logger.debug(f"Using provided video terms: {video_terms}")

    if not video_terms:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error(f"Task {task_id}: Failed to generate video terms for subject: '{params.video_subject}'.")
        return None

    return video_terms


def save_script_data(
    task_id: str, video_script: str, video_terms: List[str], params: VideoParams
):
    """
    Saves the generated script and terms to a JSON file in the task directory.

    Args:
        task_id (str): The unique identifier for the task.
        video_script (str): The generated video script.
        video_terms (List[str]): The generated search terms.
        params (VideoParams): The video parameters used.
    """
    script_file = path.join(utils.task_dir(task_id), "script.json")
    script_data = {
        "script": video_script,
        "search_terms": video_terms,
        "params": params,
    }

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(utils.to_json(script_data))


async def generate_audio(
    task_id: str, params: VideoParams, video_script: str
) -> Tuple[Optional[str], Optional[int], Optional[Any]]:
    """
    Generates audio from the script using the TTS service.

    It synthesizes the speech, saves it as an MP3 file, and returns the
    audio file path, its duration, and the SubMaker object for subtitle generation.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.
        video_script (str): The script to be converted to speech.

    Returns:
        Tuple[Optional[str], Optional[int], Optional[Any]]: A tuple containing the audio file path,
        duration in seconds, and the SubMaker object, or (None, None, None) on failure.
    """
    logger.info("[Step 2/5] Generating audio...")
    audio_file = path.join(utils.task_dir(task_id), "audio.mp3")
    
    # 🚨 FIXED: 한국어 음성 강제 적용 - Phase 1 Task 2
    voice_name = get_korean_voice_name(params)
    logger.info(f"🎤 Using voice: {voice_name}")
    
    sub_maker = await asyncio.to_thread(
        voice.tts,
        text=video_script,
        voice_name=voice_name,
        voice_rate=params.voice_rate,
        voice_file=audio_file,
        voice_volume=params.voice_volume,
    )
    if sub_maker is None:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        logger.error(
            f"""Task {task_id}: Failed to generate audio.
1. check if the language of the voice matches the language of the video script.
2. check if the network is available. If you are in China, it is recommended to use a VPN and enable the global traffic mode.
        """.strip()
        )
        return None, None, None

    audio_duration = math.ceil(voice.get_audio_duration(sub_maker))
    return audio_file, audio_duration, sub_maker


async def generate_subtitle(
    task_id: str,
    params: VideoParams,
    video_script: str,
    sub_maker: Any,
    audio_file: str,
) -> str:
    """
    Generates a subtitle file (SRT) for the video.

    It uses either the SubMaker object from the TTS service or a speech-to-text
    service like Whisper to create the subtitles.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.
        video_script (str): The original video script for correction.
        sub_maker (Any): The SubMaker object from the TTS service.
        audio_file (str): The path to the generated audio file.

    Returns:
        str: The path to the generated subtitle file, or an empty string if disabled.
    """
    if not params.subtitle_enabled:
        return ""

    subtitle_path = path.join(utils.task_dir(task_id), f"{task_id}.srt")
    subtitle_provider = config.app.get("subtitle_provider", "edge").strip().lower()
    logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")

    subtitle_fallback = False
    if subtitle_provider == "edge":
        await asyncio.to_thread(
            voice.create_subtitle,
            text=video_script,
            sub_maker=sub_maker,
            subtitle_file=subtitle_path,
        )
        if not os.path.exists(subtitle_path):
            subtitle_fallback = True
            logger.warning("subtitle file not found, fallback to whisper")

    if subtitle_provider == "whisper" or subtitle_fallback:
        await asyncio.to_thread(
            subtitle.create, audio_file=audio_file, subtitle_file=subtitle_path
        )
        logger.info("Correcting generated subtitle...")
        await asyncio.to_thread(
            subtitle.correct,
            subtitle_file=subtitle_path,
            video_script=video_script,
            audio_file_path=audio_file,
        )

    subtitle_lines = subtitle.file_to_subtitles(subtitle_path)
    if not subtitle_lines:
        logger.warning(f"subtitle file is invalid: {subtitle_path}")
        return ""

    return subtitle_path


async def get_video_materials(
    task_id: str,
    params: VideoParams,
    video_terms: List[str],
    audio_duration: float,
) -> Optional[List[str]]:
    """
    Downloads or retrieves video materials for the final video.

    It can either use local files provided by the user or download stock
    videos from sources like Pexels or Pixabay based on the generated search terms.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.
        video_terms (List[str]): The search terms for stock videos.
        audio_duration (float): The total duration of the audio to match.

    Returns:
        Optional[List[str]]: A list of paths to the video material files, or None on failure.
    """
    if params.video_source == "local":
        logger.info("[Step 3/5] Preprocessing local video materials...")
        materials = await asyncio.to_thread(
            video.preprocess_video,
            materials=params.video_materials,
            clip_duration=params.video_clip_duration,
        )
        if not materials:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                f"Task {task_id}: No valid local materials found. Please check the provided files."
            )
            return None
        return [material_info.url for material_info in materials]
    else:
        logger.info(f"[Step 3/5] Downloading video materials from '{params.video_source}'...")
        downloaded_videos = await asyncio.to_thread(
            material.download_videos,
            task_id,
            search_terms=video_terms,
            source=params.video_source,
            video_aspect=params.video_aspect,
            video_contact_mode=params.video_concat_mode,
            audio_duration=audio_duration * params.video_count,
            max_clip_duration=params.video_clip_duration,
        )
        if not downloaded_videos:
            sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
            logger.error(
                f"Task {task_id}: Failed to download videos. This may be due to network issues or invalid API keys."
            )
            return None
        return downloaded_videos


async def generate_final_videos(
    task_id: str,
    params: VideoParams,
    downloaded_videos: List[str],
    audio_file: str,
    subtitle_path: str,
    db: Session,
    user: User,
) -> Tuple[List[str], List[str]]:
    """
    Generates the final video(s) by combining video clips, audio, and subtitles.

    This function handles the main video processing steps, including combining clips,
    adding audio and subtitles, and applying branding.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The video generation parameters.
        downloaded_videos (List[str]): A list of paths to the video material files.
        audio_file (str): The path to the main audio file.
        subtitle_path (str): The path to the subtitle file.
        db (Session): The database session.
        user (User): The user performing the task.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing a list of final branded video paths
        and a list of intermediate combined video paths.
    """
    final_video_paths = []
    branded_video_paths = []
    combined_video_paths = []
    video_concat_mode = (
        params.video_concat_mode if params.video_count == 1 else VideoConcatMode.random
    )
    video_transition_mode = params.video_transition_mode

    _progress = 50
    for i in range(params.video_count):
        index = i + 1
        combined_video_path = path.join(
            utils.task_dir(task_id), f"combined-{index}.mp4"
        )
        logger.info(f"[Step 4/5] Combining video clips for video #{index}...")
        await asyncio.to_thread(
            video.combine_videos,
            combined_video_path,
            video_paths=downloaded_videos,
            audio_file=audio_file,
            video_aspect=params.video_aspect,
            video_concat_mode=video_concat_mode,
            video_transition_mode=video_transition_mode,
            max_clip_duration=params.video_clip_duration,
            threads=params.n_threads,
        )

        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

        logger.info(f"[Step 5/5] Generating final video #{index} with audio and subtitles...")
        await asyncio.to_thread(
            video.generate_video,
            combined_video_path,
            audio_file,
            subtitle_path,
            final_video_path,
            params,
        )

        # Apply branding
        # Branding (watermark, intro/outro) is now handled inside generate_video
        # The 'final_video_path' is now the path to the branded video.
        branded_video_path = final_video_path
        
        _progress += 50 / params.video_count / 2
        sm.state.update_task(task_id, progress=_progress)

        final_video_paths.append(final_video_path)
        branded_video_paths.append(branded_video_path)
        combined_video_paths.append(combined_video_path)

    return branded_video_paths, combined_video_paths


async def start(
    task_id: str, params: VideoParams, db: Session, user: User, stop_at: str = "video"
) -> Optional[Dict[str, Any]]:
    """
    Starts and orchestrates the entire video generation task.

    This is the main entry point for a video generation task. It calls all the
    necessary sub-functions in a sequence, handling parallel execution for
    performance optimization.

    Args:
        task_id (str): The unique identifier for the task.
        params (VideoParams): The parameters for the video generation.
        db (Session): The database session.
        user (User): The user initiating the task.
        stop_at (str): A specific step to stop at (e.g., 'script', 'audio').
            Defaults to 'video'.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the paths to the generated
        artifacts (videos, script, audio, etc.), or None if the task fails.

    Raises:
        ValueError: If there's an issue with parallel task execution, such as
            failing to generate terms or audio.
    """
    logger.info(f"Starting task '{task_id}' for user '{user.email}' (stop_at: {stop_at}).")

    # Check if user has enough credits, unless they are using their own keys
    # (A more sophisticated check would see which APIs are being used)
    if not auth.user_has_own_keys(user):
        usage.check_credits(db, user)

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=5)

    if type(params.video_concat_mode) is str:
        params.video_concat_mode = VideoConcatMode(params.video_concat_mode)

    # 1. Generate script (sequential)
    video_script = await generate_script(task_id, params)
    if not video_script or "Error: " in video_script:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=10)

    if stop_at == "script":
        sm.state.update_task(
            task_id, state=const.TASK_STATE_COMPLETE, progress=100, script=video_script
        )
        return {"script": video_script}

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=20)

    # 2. Generate terms, audio, and materials in parallel
    video_terms = []
    audio_file, audio_duration, sub_maker = None, 0, None
    downloaded_videos = []

    async def _generate_terms_and_materials():
        nonlocal video_terms, downloaded_videos
        if params.video_source != "local":
            _video_terms = await generate_terms(task_id, params, video_script)
            if not _video_terms:
                raise ValueError("Failed to generate video terms.")
            video_terms = _video_terms
            save_script_data(task_id, video_script, video_terms, params)
            
            _audio_duration_for_materials = (
                audio_duration if audio_duration > 0 else len(video_script) / 4.0
            )

            _downloaded_videos = await get_video_materials(
                task_id, params, video_terms, _audio_duration_for_materials
            )
            if not _downloaded_videos:
                raise ValueError("Failed to download video materials.")
            downloaded_videos = _downloaded_videos

    async def _generate_audio_and_subtitle():
        nonlocal audio_file, audio_duration, sub_maker
        _audio_file, _audio_duration, _sub_maker = await generate_audio(task_id, params, video_script)
        if not _audio_file:
            raise ValueError("Failed to generate audio.")
        audio_file, audio_duration, sub_maker = _audio_file, _audio_duration, _sub_maker

    try:
        # Run audio generation and material acquisition in parallel
        await asyncio.gather(
            _generate_terms_and_materials(),
            _generate_audio_and_subtitle()
        )
    except ValueError as e:
        logger.error(f"Task {task_id}: A critical error occurred during parallel processing (audio/materials). Error: {e}")
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=40)

    # 3. Generate subtitle (sequential, depends on audio)
    subtitle_path = await generate_subtitle(
        task_id, params, video_script, sub_maker, audio_file
    )

    sm.state.update_task(task_id, state=const.TASK_STATE_PROCESSING, progress=40)

    # 4. Check if we should stop before video generation
    if stop_at != "video":
        # This part is simplified as the parallel execution complicates stopping at intermediate steps.
        # For a full implementation, more granular control would be needed.
        sm.state.update_task(task_id, state=const.TASK_STATE_COMPLETE, progress=100)
        return {"message": f"Task stopped at '{stop_at}' step."}

    # 5. Generate final videos
    final_video_paths, combined_video_paths = await generate_final_videos(
        task_id, params, downloaded_videos, audio_file, subtitle_path, db, user
    )

    if not final_video_paths:
        sm.state.update_task(task_id, state=const.TASK_STATE_FAILED)
        return

    logger.success(
        f"Task {task_id} completed successfully. Generated {len(final_video_paths)} video(s)."
    )

    kwargs = {
        "videos": final_video_paths,
        "combined_videos": combined_video_paths,
        "script": video_script,
        "terms": video_terms,
        "audio_file": audio_file,
        "audio_duration": audio_duration,
        "subtitle_path": subtitle_path,
        "materials": downloaded_videos,
    }
    sm.state.update_task(
        task_id, state=const.TASK_STATE_COMPLETE, progress=100, **kwargs
    )

    # Deduct credits if service keys were used
    if not auth.user_has_own_keys(user):
        usage.use_credits(db, user)

    # Save to video history
    if final_video_paths:
        history.create_video_history(
            db=db,
            task_id=task_id,
            user=user,
            video_path=final_video_paths[0],
            params=params,
        )

    return kwargs


if __name__ == "__main__":
    task_id = "task_id"
    params = VideoParams(
        video_subject="The role of money",
        voice_name="zh-CN-XiaoyiNeural-Female",
        voice_rate=1.0,
    )
    asyncio.run(start(task_id, params, db=None, user=None, stop_at="video"))

# Template service wrappers
def create_template(db: Session, template_data: TemplateCreate, user: User) -> Template:
    return template.create_template(db, template_data, user)

def get_template(db: Session, template_id: int) -> Template:
    return template.get_template(db, template_id)

def get_templates(db: Session, user_id: int) -> List[Template]:
    return template.get_templates(db, user_id)

def delete_template(db: Session, template_id: int, user: User):
    return template.delete_template(db, template_id, user)

# YouTube uploader service wrapper
def upload_to_youtube(
    user_id: str,
    file_path: str,
    title: str,
    description: str,
    tags: list,
):
    return youtube_uploader.upload_video(
        user_id=user_id,
        file_path=file_path,
        title=title,
        description=description,
        tags=tags
    )
