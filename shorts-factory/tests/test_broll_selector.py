"""
BrollSelector 모듈 테스트
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.broll_selector import BrollSelector, BrollClip, BrollConfig


class TestBrollClip:
    """BrollClip 테스트"""

    def test_creation(self, temp_dir):
        """BrollClip 생성 테스트"""
        clip = BrollClip(
            path=temp_dir / "test.mp4",
            duration=10.0,
            themes=["nature", "calm"],
            source="pexels",
            resolution="1080x1920"
        )

        assert clip.duration == 10.0
        assert "nature" in clip.themes

    def test_to_dict(self, temp_dir):
        """to_dict 테스트"""
        clip = BrollClip(
            path=temp_dir / "test.mp4",
            duration=10.0,
            themes=["nature"],
            source="pexels"
        )

        data = clip.to_dict()

        assert data['duration'] == 10.0
        assert "nature" in data['themes']
        assert data['source'] == "pexels"

    def test_from_dict(self, temp_dir):
        """from_dict 테스트"""
        data = {
            "path": str(temp_dir / "test.mp4"),
            "duration": 15.0,
            "themes": ["city", "urban"],
            "source": "pixabay",
            "resolution": "1920x1080"
        }

        clip = BrollClip.from_dict(data)

        assert clip.duration == 15.0
        assert "city" in clip.themes


class TestBrollSelector:
    """BrollSelector 테스트"""

    def test_init_empty_folder(self, temp_dir):
        """빈 폴더 초기화 테스트"""
        selector = BrollSelector(assets_path=temp_dir)

        assert len(selector.clips) == 0

    def test_theme_keywords(self):
        """테마 키워드 매핑 테스트"""
        assert "역경" in BrollSelector.THEME_KEYWORDS
        assert "storm" in BrollSelector.THEME_KEYWORDS["역경"]

    def test_extract_themes_from_path(self, temp_dir):
        """경로에서 테마 추출 테스트"""
        # nature 폴더 생성
        nature_dir = temp_dir / "nature"
        nature_dir.mkdir()
        test_file = nature_dir / "ocean_sunset.mp4"
        test_file.touch()

        selector = BrollSelector(assets_path=temp_dir)
        themes = selector._extract_themes_from_path(test_file)

        # 폴더명 또는 파일명에서 테마 추출
        assert len(themes) >= 1

    def test_filter_by_themes(self, temp_dir):
        """테마 필터링 테스트"""
        selector = BrollSelector(assets_path=temp_dir)

        # 수동으로 클립 추가
        selector.clips = [
            BrollClip(path=temp_dir / "1.mp4", duration=10, themes=["역경", "storm"]),
            BrollClip(path=temp_dir / "2.mp4", duration=10, themes=["마음", "peace"]),
            BrollClip(path=temp_dir / "3.mp4", duration=10, themes=["역경", "mountain"]),
        ]

        filtered = selector._filter_by_themes(["역경"])

        assert len(filtered) == 2

    def test_select_empty(self, temp_dir):
        """클립이 없을 때 선택 테스트"""
        selector = BrollSelector(assets_path=temp_dir)
        result = selector.select(["역경"], 30.0)

        assert result == []

    def test_select_with_clips(self, temp_dir):
        """클립 선택 테스트"""
        selector = BrollSelector(assets_path=temp_dir)

        # 수동으로 클립 추가
        selector.clips = [
            BrollClip(path=temp_dir / "1.mp4", duration=10, themes=["역경"]),
            BrollClip(path=temp_dir / "2.mp4", duration=15, themes=["역경"]),
            BrollClip(path=temp_dir / "3.mp4", duration=20, themes=["마음"]),
        ]

        selected = selector.select(["역경"], 25.0)

        # 최소한 25초를 채울 만큼 선택되어야 함
        total_duration = sum(c.duration for c in selected)
        assert total_duration >= 25.0

    def test_get_stats(self, temp_dir):
        """통계 조회 테스트"""
        selector = BrollSelector(assets_path=temp_dir)

        selector.clips = [
            BrollClip(path=temp_dir / "1.mp4", duration=10, themes=["역경"]),
            BrollClip(path=temp_dir / "2.mp4", duration=20, themes=["마음"]),
        ]

        stats = selector.get_stats()

        assert stats['total_clips'] == 2
        assert stats['total_duration'] == 30.0
        assert stats['avg_duration'] == 15.0
        assert "역경" in stats['themes']
        assert "마음" in stats['themes']

    def test_save_and_load_index(self, temp_dir):
        """인덱스 저장/로드 테스트"""
        selector = BrollSelector(assets_path=temp_dir)

        selector.clips = [
            BrollClip(path=temp_dir / "1.mp4", duration=10, themes=["역경"]),
        ]

        selector.save_index()

        # 새로운 인스턴스로 로드
        selector2 = BrollSelector(assets_path=temp_dir)

        assert len(selector2.clips) == 1
        assert selector2.clips[0].duration == 10
