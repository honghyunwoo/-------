"""
자막 생성 모듈
스크립트 기반 SRT 자막 파일 생성
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class SubtitleEntry:
    """자막 항목"""
    index: int
    start_time: float  # 초 단위
    end_time: float  # 초 단위
    text: str

    def to_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 형식으로 변환 (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def to_srt(self) -> str:
        """SRT 형식 문자열 반환"""
        start = self.to_srt_time(self.start_time)
        end = self.to_srt_time(self.end_time)
        return f"{self.index}\n{start} --> {end}\n{self.text}\n"


@dataclass
class SubtitleConfig:
    """자막 설정 - 짧고 읽기 쉬운 자막"""
    max_chars_per_line: int = 12  # 한 줄 최대 12자 (가독성 향상)
    max_lines: int = 2            # 최대 2줄
    min_duration: float = 1.0     # 최소 1초 표시 (읽을 시간)
    gap_between: float = 0.05     # 자막 간 간격 (초)
    split_long_sentences: bool = True  # 긴 문장 자동 분리


class SubtitleGenerator:
    """자막 생성기"""

    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()

    def generate_from_script(
        self,
        script_text: str,
        audio_duration: float,
        output_path: Path
    ) -> Path:
        """스크립트 기반 자막 생성"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 문장 분리
        sentences = self._split_sentences(script_text)

        # 2. 시간 계산
        entries = self._calculate_timings(sentences, audio_duration)

        # 3. 줄바꿈 처리
        entries = self._apply_line_breaks(entries)

        # 4. SRT 파일 작성
        return self._write_srt(entries, output_path)

    def generate_from_segments(
        self,
        segments: List[dict],
        output_path: Path
    ) -> Path:
        """
        Whisper 세그먼트에서 자막 생성
        segments: [{"start": 0.0, "end": 2.5, "text": "..."}, ...]
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        entries = []
        for i, seg in enumerate(segments, 1):
            entry = SubtitleEntry(
                index=i,
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"].strip()
            )
            entries.append(entry)

        entries = self._apply_line_breaks(entries)
        return self._write_srt(entries, output_path)

    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리 - 짧은 단위로 분리"""
        # 섹션 마커 제거 [훅], [명언] 등
        text = re.sub(r'\[.*?\]', '', text)

        # 줄바꿈을 공백으로
        text = text.replace('\n', ' ')

        # 1차: 마침표, 물음표, 느낌표로 분리
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]

        # 2차: 긴 문장 추가 분리 (쉼표, 접속사 기준)
        if self.config.split_long_sentences:
            split_sentences = []
            for sentence in sentences:
                if len(sentence) > 25:  # 25자 이상이면 분리
                    # 쉼표, 접속사로 분리
                    parts = re.split(r'(?<=[,，])\s*|(?=그리고|하지만|그러나|그래서|왜냐하면)', sentence)
                    parts = [p.strip() for p in parts if p.strip()]
                    split_sentences.extend(parts)
                else:
                    split_sentences.append(sentence)
            sentences = split_sentences

        return sentences

    def _calculate_timings(
        self,
        sentences: List[str],
        total_duration: float
    ) -> List[SubtitleEntry]:
        """문장별 타이밍 계산"""
        if not sentences:
            return []

        # 총 글자 수 계산
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            return []

        # 각 문장에 비례 시간 할당
        entries = []
        current_time = 0.0

        for i, sentence in enumerate(sentences, 1):
            # 글자 수 비례로 시간 계산
            char_ratio = len(sentence) / total_chars
            duration = max(
                total_duration * char_ratio,
                self.config.min_duration
            )

            # 끝 시간이 총 시간을 넘지 않도록
            end_time = min(current_time + duration, total_duration)

            entry = SubtitleEntry(
                index=i,
                start_time=current_time,
                end_time=end_time - self.config.gap_between,
                text=sentence
            )
            entries.append(entry)

            current_time = end_time

        return entries

    def _apply_line_breaks(
        self,
        entries: List[SubtitleEntry]
    ) -> List[SubtitleEntry]:
        """줄바꿈 적용"""
        for entry in entries:
            entry.text = self._wrap_text(
                entry.text,
                self.config.max_chars_per_line,
                self.config.max_lines
            )
        return entries

    # 분리 금지 패턴: 앞 단어 + 뒷 단어를 붙여서 유지
    # (앞 단어 끝, 뒷 단어 시작) 조합
    KEEP_TOGETHER_PATTERNS = [
        # 관형사형 + 의존명사 (할 일, 볼 것, 갈 곳 등)
        ("할", "일"), ("볼", "것"), ("갈", "곳"), ("쓸", "곳"),
        ("할", "것"), ("볼", "일"), ("할", "수"), ("될", "수"),
        ("알", "수"), ("갈", "수"), ("올", "수"), ("볼", "수"),
        # 숫자 + 단위
        ("1", "분"), ("2", "분"), ("3", "분"), ("5", "분"), ("10", "분"),
        ("1", "초"), ("2", "초"), ("5", "초"), ("10", "초"),
        ("1", "개"), ("2", "개"), ("3", "개"),
        ("한", "번"), ("두", "번"), ("세", "번"),
        ("한", "개"), ("두", "개"), ("세", "개"),
        # 부사 + 동사/형용사
        ("더", "쉽"), ("더", "빨"), ("더", "좋"), ("더", "나"),
        ("아주", "작"), ("아주", "쉬"), ("아주", "좋"),
        # 일반적 복합어
        ("그게", "시작"), ("아직", "포기"),
    ]

    def _should_keep_together(self, word1: str, word2: str) -> bool:
        """두 단어를 붙여야 하는지 확인"""
        for pattern1, pattern2 in self.KEEP_TOGETHER_PATTERNS:
            if word1.endswith(pattern1) or word1 == pattern1:
                if word2.startswith(pattern2) or word2 == pattern2:
                    return True
        return False

    def _wrap_text(
        self,
        text: str,
        max_chars: int,
        max_lines: int
    ) -> str:
        """텍스트 줄바꿈 - 한국어 복합어 고려"""
        if len(text) <= max_chars:
            return text

        words = text.split()
        if not words:
            return text

        # 1단계: 분리 금지 단어쌍 병합
        merged_words = []
        i = 0
        while i < len(words):
            if i + 1 < len(words) and self._should_keep_together(words[i], words[i + 1]):
                # 두 단어를 공백 포함해서 병합
                merged_words.append(f"{words[i]} {words[i + 1]}")
                i += 2
            else:
                merged_words.append(words[i])
                i += 1

        # 2단계: 줄바꿈 적용
        lines = []
        current_line = ""

        for word in merged_words:
            test_line = f"{current_line} {word}".strip()

            if len(test_line) <= max_chars:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

                # 최대 줄 수 체크
                if len(lines) >= max_lines - 1:
                    # 나머지 단어들 모두 현재 줄에
                    remaining_idx = merged_words.index(word)
                    current_line = ' '.join(merged_words[remaining_idx:])
                    break

        if current_line:
            lines.append(current_line)

        return '\n'.join(lines[:max_lines])

    def _write_srt(
        self,
        entries: List[SubtitleEntry],
        output_path: Path
    ) -> Path:
        """SRT 파일 작성"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(entry.to_srt())
                f.write('\n')

        return output_path

    def parse_srt(self, srt_path: Path) -> List[SubtitleEntry]:
        """SRT 파일 파싱"""
        entries = []

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # SRT 블록 분리
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])

                    # 시간 파싱
                    time_match = re.match(
                        r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})',
                        lines[1]
                    )
                    if time_match:
                        start = self._parse_srt_time(time_match.group(1))
                        end = self._parse_srt_time(time_match.group(2))
                        text = '\n'.join(lines[2:])

                        entries.append(SubtitleEntry(
                            index=index,
                            start_time=start,
                            end_time=end,
                            text=text
                        ))
                except (ValueError, IndexError):
                    continue

        return entries

    def _parse_srt_time(self, time_str: str) -> float:
        """SRT 시간 문자열을 초로 변환"""
        match = re.match(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3})',
            time_str
        )
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            return hours * 3600 + minutes * 60 + seconds + millis / 1000
        return 0.0


class WhisperSubtitleGenerator(SubtitleGenerator):
    """Whisper 기반 자막 생성기"""

    def __init__(self, model_size: str = "base", config: SubtitleConfig = None):
        super().__init__(config)
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Whisper 모델 로드 (지연 로딩)"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"
                )
            except ImportError:
                raise ImportError(
                    "faster-whisper가 설치되지 않았습니다. "
                    "pip install faster-whisper"
                )
        return self._model

    def generate_from_audio(
        self,
        audio_path: Path,
        output_path: Path,
        language: str = "ko"
    ) -> Path:
        """오디오에서 자막 추출 (Whisper)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        model = self._load_model()

        # Whisper 전사
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            word_timestamps=True
        )

        # 세그먼트를 자막 엔트리로 변환
        entries = []
        for i, segment in enumerate(segments, 1):
            entry = SubtitleEntry(
                index=i,
                start_time=segment.start,
                end_time=segment.end,
                text=segment.text.strip()
            )
            entries.append(entry)

        # 줄바꿈 처리 및 저장
        entries = self._apply_line_breaks(entries)
        return self._write_srt(entries, output_path)
