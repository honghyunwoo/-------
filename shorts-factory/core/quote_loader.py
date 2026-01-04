"""
명언 로더 모듈
quotes_library.json에서 명언을 로드하고 관리
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json
import random


@dataclass
class Quote:
    """명언 데이터 클래스"""
    id: int
    text: str
    author: str
    source: str
    themes: List[str]
    text_original: str = ""
    author_en: str = ""
    used_count: int = 0
    last_used: Optional[str] = None


class QuoteNotFoundError(Exception):
    """명언을 찾을 수 없을 때 발생하는 예외"""
    pass


class QuoteLoader:
    """명언 라이브러리 로더 및 관리자"""

    def __init__(self, library_path: str | Path):
        """
        Args:
            library_path: quotes_library.json 파일 경로
        """
        self.library_path = Path(library_path)
        self.quotes: List[Quote] = []
        self._load_library()

    def _load_library(self) -> None:
        """JSON 파일에서 명언 라이브러리 로드"""
        if not self.library_path.exists():
            raise FileNotFoundError(f"명언 라이브러리를 찾을 수 없습니다: {self.library_path}")

        with open(self.library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.quotes = []
        for q in data.get('quotes', []):
            quote = Quote(
                id=q['id'],
                text=q['text'],
                author=q['author'],
                source=q['source'],
                themes=q.get('themes', []),
                text_original=q.get('text_original', ''),
                author_en=q.get('author_en', ''),
                used_count=q.get('used_count', 0),
                last_used=q.get('last_used')
            )
            self.quotes.append(quote)

    def _save_library(self) -> None:
        """변경사항을 JSON 파일에 저장"""
        data = {
            'quotes': [
                {
                    'id': q.id,
                    'text': q.text,
                    'text_original': q.text_original,
                    'author': q.author,
                    'author_en': q.author_en,
                    'source': q.source,
                    'themes': q.themes,
                    'used_count': q.used_count,
                    'last_used': q.last_used
                }
                for q in self.quotes
            ],
            'metadata': {
                'version': '1.0',
                'total_quotes': len(self.quotes),
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
        }

        with open(self.library_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_by_id(self, quote_id: int) -> Quote:
        """
        ID로 명언 조회

        Args:
            quote_id: 명언 ID

        Returns:
            Quote 객체

        Raises:
            QuoteNotFoundError: 해당 ID의 명언이 없을 때
        """
        for quote in self.quotes:
            if quote.id == quote_id:
                return quote
        raise QuoteNotFoundError(f"ID {quote_id}인 명언을 찾을 수 없습니다.")

    def get_random(self, theme: Optional[str] = None) -> Quote:
        """
        랜덤 명언 선택

        Args:
            theme: 특정 테마로 필터링 (선택)

        Returns:
            랜덤하게 선택된 Quote 객체
        """
        candidates = self.quotes

        if theme:
            candidates = [q for q in self.quotes if theme in q.themes]
            if not candidates:
                candidates = self.quotes  # 테마 매칭 없으면 전체에서 선택

        return random.choice(candidates)

    def get_unused(self, limit: int = 10) -> List[Quote]:
        """
        사용하지 않은 또는 가장 적게 사용된 명언 목록

        Args:
            limit: 반환할 최대 개수

        Returns:
            사용 횟수가 적은 순으로 정렬된 명언 리스트
        """
        sorted_quotes = sorted(self.quotes, key=lambda q: q.used_count)
        return sorted_quotes[:limit]

    def get_by_author(self, author: str) -> List[Quote]:
        """
        저자별 명언 조회

        Args:
            author: 저자 이름

        Returns:
            해당 저자의 명언 리스트
        """
        return [q for q in self.quotes if q.author == author]

    def get_by_theme(self, theme: str) -> List[Quote]:
        """
        테마별 명언 조회

        Args:
            theme: 테마 이름

        Returns:
            해당 테마의 명언 리스트
        """
        return [q for q in self.quotes if theme in q.themes]

    def mark_used(self, quote_id: int) -> None:
        """
        명언 사용 표시

        Args:
            quote_id: 사용한 명언 ID
        """
        for quote in self.quotes:
            if quote.id == quote_id:
                quote.used_count += 1
                quote.last_used = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_library()
                return

    def search(self, keyword: str) -> List[Quote]:
        """
        키워드로 명언 검색

        Args:
            keyword: 검색 키워드

        Returns:
            키워드가 포함된 명언 리스트
        """
        keyword = keyword.lower()
        return [
            q for q in self.quotes
            if keyword in q.text.lower()
            or keyword in q.author.lower()
            or any(keyword in theme.lower() for theme in q.themes)
        ]

    def list_all(self) -> List[Quote]:
        """모든 명언 반환"""
        return self.quotes

    def count(self) -> int:
        """전체 명언 개수"""
        return len(self.quotes)

    def get_stats(self) -> dict:
        """명언 라이브러리 통계"""
        authors = {}
        themes = {}

        for q in self.quotes:
            # 저자별 집계
            authors[q.author] = authors.get(q.author, 0) + 1

            # 테마별 집계
            for theme in q.themes:
                themes[theme] = themes.get(theme, 0) + 1

        return {
            'total': len(self.quotes),
            'by_author': authors,
            'by_theme': themes,
            'used': sum(1 for q in self.quotes if q.used_count > 0),
            'unused': sum(1 for q in self.quotes if q.used_count == 0)
        }


if __name__ == '__main__':
    # 테스트
    loader = QuoteLoader('templates/stoic/quotes_library.json')
    print(f"총 {loader.count()}개의 명언 로드됨")

    quote = loader.get_by_id(1)
    print(f"\n명언 #1: {quote.text[:50]}...")
    print(f"저자: {quote.author}")

    random_quote = loader.get_random()
    print(f"\n랜덤 명언: {random_quote.text[:50]}...")

    stats = loader.get_stats()
    print(f"\n통계: {stats}")
