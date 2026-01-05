"""
Pytest fixtures for Shorts Factory tests
"""

import pytest
from pathlib import Path
import tempfile
import json


@pytest.fixture
def temp_dir():
    """임시 디렉토리 제공"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_quote_data():
    """테스트용 명언 데이터"""
    return {
        "quotes": [
            {
                "id": 1,
                "text": "장애물이 곧 길이 된다.",
                "author": "마르쿠스 아우렐리우스",
                "source": "명상록",
                "themes": ["역경", "성장"],
                "used_count": 0,
                "last_used": None
            },
            {
                "id": 2,
                "text": "우리가 통제할 수 있는 것에 집중하라.",
                "author": "에픽테토스",
                "source": "엥케이리디온",
                "themes": ["통제", "마음"],
                "used_count": 1,
                "last_used": "2026-01-01"
            }
        ]
    }


@pytest.fixture
def sample_quotes_file(temp_dir, sample_quote_data):
    """테스트용 명언 JSON 파일"""
    quotes_path = temp_dir / "quotes_library.json"
    with open(quotes_path, 'w', encoding='utf-8') as f:
        json.dump(sample_quote_data, f, ensure_ascii=False)
    return quotes_path


@pytest.fixture
def sample_srt_content():
    """테스트용 SRT 파일 내용"""
    return """1
00:00:00,000 --> 00:00:03,000
장애물이 곧 길이 된다.

2
00:00:03,000 --> 00:00:07,000
이것은 스토아 철학의 핵심입니다.

3
00:00:07,000 --> 00:00:10,000
오늘 실천해보세요.
"""


@pytest.fixture
def sample_srt_file(temp_dir, sample_srt_content):
    """테스트용 SRT 파일"""
    srt_path = temp_dir / "test.srt"
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(sample_srt_content)
    return srt_path
