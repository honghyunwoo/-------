"""
SubtitleGenerator 모듈 테스트
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.subtitle_generator import SubtitleGenerator, SubtitleEntry, SubtitleConfig


class TestSubtitleEntry:
    """SubtitleEntry 테스트"""

    def test_to_srt_time(self):
        """SRT 시간 변환 테스트"""
        entry = SubtitleEntry(
            index=1,
            start_time=0.0,
            end_time=3.5,
            text="테스트"
        )

        assert entry.to_srt_time(0.0) == "00:00:00,000"
        assert entry.to_srt_time(3.5) == "00:00:03,500"
        assert entry.to_srt_time(65.123) == "00:01:05,123"
        assert entry.to_srt_time(3661.5) == "01:01:01,500"

    def test_to_srt(self):
        """SRT 형식 출력 테스트"""
        entry = SubtitleEntry(
            index=1,
            start_time=0.0,
            end_time=3.0,
            text="테스트 자막"
        )

        srt = entry.to_srt()

        assert "1\n" in srt
        assert "00:00:00,000 --> 00:00:03,000" in srt
        assert "테스트 자막" in srt


class TestSubtitleGenerator:
    """SubtitleGenerator 테스트"""

    def test_init_default_config(self):
        """기본 설정 초기화 테스트"""
        gen = SubtitleGenerator()

        assert gen.config.max_chars_per_line == 15
        assert gen.config.max_lines == 2

    def test_init_custom_config(self):
        """커스텀 설정 초기화 테스트"""
        config = SubtitleConfig(max_chars_per_line=20, max_lines=3)
        gen = SubtitleGenerator(config=config)

        assert gen.config.max_chars_per_line == 20
        assert gen.config.max_lines == 3

    def test_generate_from_script(self, temp_dir):
        """스크립트에서 자막 생성 테스트"""
        gen = SubtitleGenerator()
        script = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
        output_path = temp_dir / "output.srt"

        result = gen.generate_from_script(script, 10.0, output_path)

        assert result.exists()
        content = result.read_text(encoding='utf-8')
        assert "첫 번째" in content or "문장" in content

    def test_parse_srt(self, sample_srt_file):
        """SRT 파일 파싱 테스트"""
        gen = SubtitleGenerator()
        entries = gen.parse_srt(sample_srt_file)

        assert len(entries) == 3
        assert entries[0].index == 1
        assert entries[0].start_time == 0.0
        assert entries[0].end_time == 3.0
        assert "장애물" in entries[0].text

    def test_parse_srt_time(self):
        """SRT 시간 파싱 테스트"""
        gen = SubtitleGenerator()

        assert gen._parse_srt_time("00:00:00,000") == 0.0
        assert gen._parse_srt_time("00:00:03,500") == 3.5
        assert gen._parse_srt_time("00:01:05,123") == 65.123
        assert gen._parse_srt_time("01:01:01,500") == 3661.5

    def test_split_sentences(self):
        """문장 분리 테스트"""
        gen = SubtitleGenerator()

        # 기본 분리
        sentences = gen._split_sentences("첫 번째. 두 번째! 세 번째?")
        assert len(sentences) == 3

        # 섹션 마커 제거
        sentences = gen._split_sentences("[훅] 질문입니다? [명언] 명언입니다.")
        assert "[훅]" not in sentences[0]
        assert "[명언]" not in sentences[-1]

    def test_wrap_text(self):
        """텍스트 줄바꿈 테스트"""
        gen = SubtitleGenerator()

        # 짧은 텍스트는 그대로
        result = gen._wrap_text("짧은 텍스트", 20, 2)
        assert result == "짧은 텍스트"

        # 긴 텍스트는 줄바꿈
        result = gen._wrap_text("이것은 매우 긴 텍스트입니다 줄바꿈이 필요합니다", 10, 2)
        assert "\n" in result

    def test_calculate_timings(self):
        """타이밍 계산 테스트"""
        gen = SubtitleGenerator()
        sentences = ["짧은 문장.", "이것은 조금 더 긴 문장입니다."]

        entries = gen._calculate_timings(sentences, 10.0)

        assert len(entries) == 2
        assert entries[0].start_time == 0.0
        assert entries[-1].end_time <= 10.0

        # 긴 문장이 더 긴 시간을 가져야 함
        duration1 = entries[0].end_time - entries[0].start_time
        duration2 = entries[1].end_time - entries[1].start_time
        assert duration2 > duration1
