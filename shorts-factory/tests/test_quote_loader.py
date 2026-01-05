"""
QuoteLoader 모듈 테스트
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quote_loader import QuoteLoader, Quote, QuoteNotFoundError


class TestQuoteLoader:
    """QuoteLoader 테스트"""

    def test_load_quotes(self, sample_quotes_file):
        """명언 로드 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        assert loader.count() == 2

    def test_get_by_id(self, sample_quotes_file):
        """ID로 명언 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        quote = loader.get_by_id(1)

        assert quote.id == 1
        assert quote.author == "마르쿠스 아우렐리우스"
        assert "역경" in quote.themes

    def test_get_by_id_not_found(self, sample_quotes_file):
        """존재하지 않는 ID 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)

        with pytest.raises(QuoteNotFoundError):
            loader.get_by_id(999)

    def test_get_unused(self, sample_quotes_file):
        """미사용 명언 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        unused = loader.get_unused(limit=5)

        # used_count=0인 명언이 먼저 나와야 함
        assert len(unused) >= 1
        assert unused[0].used_count == 0

    def test_get_random(self, sample_quotes_file):
        """랜덤 명언 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        quote = loader.get_random()

        assert isinstance(quote, Quote)
        assert quote.id in [1, 2]

    def test_get_by_theme(self, sample_quotes_file):
        """테마별 명언 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        quotes = loader.get_by_theme("역경")

        assert len(quotes) >= 1
        assert all("역경" in q.themes for q in quotes)

    def test_mark_used(self, sample_quotes_file):
        """사용 표시 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        original_count = loader.get_by_id(1).used_count

        loader.mark_used(1)

        # 다시 로드해서 확인
        loader2 = QuoteLoader(sample_quotes_file)
        assert loader2.get_by_id(1).used_count == original_count + 1

    def test_list_all(self, sample_quotes_file):
        """전체 목록 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        quotes = loader.list_all()

        assert len(quotes) == 2
        assert all(isinstance(q, Quote) for q in quotes)

    def test_get_stats(self, sample_quotes_file):
        """통계 조회 테스트"""
        loader = QuoteLoader(sample_quotes_file)
        stats = loader.get_stats()

        assert stats['total'] == 2
        assert stats['used'] == 1  # used_count > 0인 것
        assert stats['unused'] == 1


class TestQuote:
    """Quote 데이터클래스 테스트"""

    def test_quote_creation(self):
        """Quote 객체 생성 테스트"""
        quote = Quote(
            id=1,
            text="테스트 명언",
            author="테스트 저자",
            source="테스트 출처",
            themes=["테마1", "테마2"],
            used_count=0,
            last_used=None
        )

        assert quote.id == 1
        assert quote.text == "테스트 명언"
        assert len(quote.themes) == 2

    def test_quote_as_dict(self):
        """Quote dataclass to dict 변환 테스트"""
        from dataclasses import asdict

        quote = Quote(
            id=1,
            text="테스트",
            author="저자",
            source="출처",
            themes=["테마"],
            used_count=0,
            last_used=None
        )

        data = asdict(quote)

        assert data['id'] == 1
        assert data['text'] == "테스트"
        assert 'themes' in data
