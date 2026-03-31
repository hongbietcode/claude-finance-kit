"""Data models for Perplexity search results."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    """A single search result from Perplexity."""

    title: str
    url: str
    snippet: str
    date: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "date": self.date,
        }


@dataclass
class SearchResponse:
    """Aggregated response from a Perplexity search call."""

    query: str
    results: List[SearchResult] = field(default_factory=list)

    def to_dict_list(self) -> List[dict]:
        return [r.to_dict() for r in self.results]
