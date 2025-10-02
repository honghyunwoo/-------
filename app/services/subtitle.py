import json
import os.path
import re
from timeit import default_timer as timer

from faster_whisper import WhisperModel
from loguru import logger

from app.config import config
from app.utils import utils

model_size = config.whisper.get("model_size", "large-v3")
device = config.whisper.get("device", "cpu")
compute_type = config.whisper.get("compute_type", "int8")
model = None


def create(audio_file, subtitle_file: str = ""):
    global model
    if not model:
        model_path = f"{utils.root_dir()}/models/whisper-{model_size}"
        model_bin_file = f"{model_path}/model.bin"
        if not os.path.isdir(model_path) or not os.path.isfile(model_bin_file):
            model_path = model_size

        logger.info(
            f"loading model: {model_path}, device: {device}, compute_type: {compute_type}"
        )
        try:
            model = WhisperModel(
                model_size_or_path=model_path, device=device, compute_type=compute_type
            )
        except Exception as e:
            logger.error(
                f"failed to load model: {e} \n\n"
                f"********************************************\n"
                f"this may be caused by network issue. \n"
                f"please download the model manually and put it in the 'models' folder. \n"
                f"see README.md FAQ for more details.\n"
                f"********************************************\n\n"
            )
            return None

    logger.info(f"start, output file: {subtitle_file}")
    if not subtitle_file:
        subtitle_file = f"{audio_file}.srt"

    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    logger.info(
        f"detected language: '{info.language}', probability: {info.language_probability:.2f}"
    )

    start = timer()
    subtitles = []

    def recognized(seg_text, seg_start, seg_end):
        seg_text = seg_text.strip()
        if not seg_text:
            return

        msg = "[%.2fs -> %.2fs] %s" % (seg_start, seg_end, seg_text)
        logger.debug(msg)

        subtitles.append(
            {"msg": seg_text, "start_time": seg_start, "end_time": seg_end}
        )

    for segment in segments:
        words_idx = 0
        words_len = len(segment.words)

        seg_start = 0
        seg_end = 0
        seg_text = ""

        if segment.words:
            is_segmented = False
            for word in segment.words:
                if not is_segmented:
                    seg_start = word.start
                    is_segmented = True

                seg_end = word.end
                # If it contains punctuation, then break the sentence.
                seg_text += word.word

                if utils.str_contains_punctuation(word.word):
                    # remove last char
                    seg_text = seg_text[:-1]
                    if not seg_text:
                        continue

                    recognized(seg_text, seg_start, seg_end)

                    is_segmented = False
                    seg_text = ""

                if words_idx == 0 and segment.start < word.start:
                    seg_start = word.start
                if words_idx == (words_len - 1) and segment.end > word.end:
                    seg_end = word.end
                words_idx += 1

        if not seg_text:
            continue

        recognized(seg_text, seg_start, seg_end)

    end = timer()

    diff = end - start
    logger.info(f"complete, elapsed: {diff:.2f} s")

    idx = 1
    lines = []
    for subtitle in subtitles:
        text = subtitle.get("msg")
        if text:
            lines.append(
                utils.text_to_srt(
                    idx, text, subtitle.get("start_time"), subtitle.get("end_time")
                )
            )
            idx += 1

    sub = "\n".join(lines) + "\n"
    with open(subtitle_file, "w", encoding="utf-8") as f:
        f.write(sub)
    logger.info(f"subtitle file created: {subtitle_file}")


def file_to_subtitles(filename):
    if not filename or not os.path.isfile(filename):
        return []

    times_texts = []
    current_times = None
    current_text = ""
    index = 0
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            times = re.findall("([0-9]*:[0-9]*:[0-9]*,[0-9]*)", line)
            if times:
                current_times = line
            elif line.strip() == "" and current_times:
                index += 1
                times_texts.append((index, current_times.strip(), current_text.strip()))
                current_times, current_text = None, ""
            elif current_times:
                current_text += line
    return times_texts


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity(a, b):
    distance = levenshtein_distance(a.lower(), b.lower())
    max_length = max(len(a), len(b))
    return 1 - (distance / max_length)


def correct(subtitle_file, video_script, audio_file_path=None):
    """
    자막 동기화 완전 수정 - Phase 1 Task 1
    오디오 길이를 정확히 측정하고 자막 타이밍을 올바르게 계산합니다.
    """
    subtitle_items = file_to_subtitles(subtitle_file)
    script_lines = utils.split_string_by_punctuations(video_script)

    # 🚨 FIXED: 오디오 파일 길이 정확 측정
    audio_duration = get_accurate_audio_duration(audio_file_path, video_script)
    logger.info(f"🎯 Audio duration: {audio_duration:.2f} seconds")

    corrected = False
    new_subtitle_items = []
    
    if not script_lines:
        logger.warning("Video script is empty. Cannot correct subtitles.")
        return

    # 🚨 FIXED: 정확한 타이밍 계산
    new_subtitle_items = calculate_subtitle_timing(script_lines, audio_duration)
    
    if new_subtitle_items:
        # 🚨 FIXED: SRT 파일 생성 및 검증
        corrected = write_and_validate_srt(subtitle_file, new_subtitle_items)
        
        if corrected:
            logger.info("✅ Subtitle corrected with accurate timing")
        else:
            logger.error("❌ Subtitle correction failed")
    else:
        logger.error("❌ Failed to calculate subtitle timing")


def get_accurate_audio_duration(audio_file_path, video_script):
    """
    오디오 파일 길이를 정확히 측정합니다.
    """
    audio_duration = 0
    
    if audio_file_path and os.path.isfile(audio_file_path):
        try:
            from moviepy.editor import AudioFileClip
            with AudioFileClip(audio_file_path) as audio_clip:
                audio_duration = audio_clip.duration
            logger.info(f"🎵 Measured audio duration: {audio_duration:.2f} seconds")
        except Exception as e:
            logger.warning(f"⚠️ Failed to measure audio duration: {e}")
            audio_duration = 0

    if audio_duration == 0:
        # 🚨 FIXED: 더 정확한 추정 (한국어 기준)
        # 한국어 평균 읽기 속도: 3-4자/초
        estimated_duration = len(video_script) / 3.5
        logger.info(f"📝 Estimated audio duration: {estimated_duration:.2f} seconds")
        audio_duration = estimated_duration

    return audio_duration


def calculate_subtitle_timing(script_lines, audio_duration):
    """
    자막 타이밍을 정확히 계산합니다.
    """
    new_subtitle_items = []
    total_script_chars = sum(len(line) for line in script_lines)
    
    if total_script_chars == 0:
        logger.warning("Video script has no content. Cannot calculate timing.")
        return []

    current_time = 0.0
    
    for i, line in enumerate(script_lines):
        line = line.strip()
        if not line:
            continue

        # 🚨 FIXED: 정확한 타이밍 계산
        line_chars = len(line)
        duration = (line_chars / total_script_chars) * audio_duration
        
        # 최소 1초, 최대 5초로 제한
        duration = max(1.0, min(duration, 5.0))

        start_time = current_time
        end_time = min(current_time + duration, audio_duration)

        # 🚨 FIXED: 0초 타이밍 방지
        if start_time >= end_time:
            end_time = start_time + 1.0

        start_time_srt = utils.time_convert_seconds_to_hmsm(start_time)
        end_time_srt = utils.time_convert_seconds_to_hmsm(end_time)

        new_subtitle_items.append(
            (
                len(new_subtitle_items) + 1,
                f"{start_time_srt} --> {end_time_srt}",
                line,
            )
        )
        current_time = end_time

    return new_subtitle_items


def write_and_validate_srt(subtitle_file, new_subtitle_items):
    """
    SRT 파일을 생성하고 검증합니다.
    """
    try:
        with open(subtitle_file, "w", encoding="utf-8") as fd:
            for i, item in enumerate(new_subtitle_items):
                fd.write(f"{i + 1}\n{item[1]}\n{item[2]}\n\n")
        
        # 🚨 FIXED: 생성된 SRT 파일 검증
        if validate_srt_timing(subtitle_file):
            logger.info("✅ SRT file created and validated successfully")
            return True
        else:
            logger.error("❌ SRT file validation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to write SRT file: {e}")
        return False


def validate_srt_timing(srt_file):
    """
    생성된 SRT 파일의 타이밍을 검증합니다.
    """
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        timing_errors = 0
        
        for i, line in enumerate(lines):
            if '-->' in line:
                # 0초 타이밍 검사
                if '00:00:00,000' in line:
                    logger.error(f"❌ Subtitle timing error at line {i+1}: {line}")
                    timing_errors += 1
                
                # 타이밍 형식 검사
                if not re.match(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', line):
                    logger.error(f"❌ Invalid timing format at line {i+1}: {line}")
                    timing_errors += 1
        
        if timing_errors == 0:
            logger.info("✅ All subtitle timings are valid")
            return True
        else:
            logger.error(f"❌ Found {timing_errors} timing errors")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to validate SRT file: {e}")
        return False


if __name__ == "__main__":
    task_id = "c12fd1e6-4b0a-4d65-a075-c87abe35a072"
    task_dir = utils.task_dir(task_id)
    subtitle_file = f"{task_dir}/subtitle.srt"
    audio_file = f"{task_dir}/audio.mp3"

    subtitles = file_to_subtitles(subtitle_file)
    print(subtitles)

    script_file = f"{task_dir}/script.json"
    with open(script_file, "r") as f:
        script_content = f.read()
    s = json.loads(script_content)
    script = s.get("script")

    correct(subtitle_file, script)

    subtitle_file = f"{task_dir}/subtitle-test.srt"
    create(audio_file, subtitle_file)
