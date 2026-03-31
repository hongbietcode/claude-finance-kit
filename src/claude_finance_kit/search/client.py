"""Perplexity AI search client — generic search, AI agent decides the query."""

import os
from typing import List, Optional, Union

from claude_finance_kit.news.core.base import setup_logger
from claude_finance_kit.search.models import SearchResponse, SearchResult


class PerplexitySearch:
    """
    Generic search client backed by the Perplexity Search API.

    The caller (AI agent) decides what to search for by crafting the query.
    This client only handles API communication and result parsing.

    Usage::

        search = PerplexitySearch()
        results = search.search("FPT earnings Q1 2025")
        results = search.search("US Fed rate decision impact on Vietnam")
        results = search.search("kinh tế vĩ mô Việt Nam lãi suất 2025")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        country: str = "VN",
        max_results: int = 10,
        max_tokens_per_page: int = 1024,
        debug: bool = False,
    ) -> None:
        self.logger = setup_logger(self.__class__.__name__, debug)
        self._api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Perplexity API key not found. Set the PERPLEXITY_API_KEY environment variable or pass api_key=..."
            )
        self.country = country
        self.max_results = max_results
        self.max_tokens_per_page = max_tokens_per_page
        self._client = self._build_client()

    def _build_client(self):
        try:
            from perplexity import Perplexity

            return Perplexity(api_key=self._api_key)
        except ImportError as exc:
            raise ImportError("perplexityai package is required. Install with: pip install perplexityai") from exc

    def _parse_results(self, raw_results) -> List[SearchResult]:
        return [
            SearchResult(
                title=r.title or "",
                url=r.url or "",
                snippet=getattr(r, "snippet", "") or "",
                date=getattr(r, "date", None),
            )
            for r in raw_results
        ]

    def _call_api(
        self,
        query: Union[str, List[str]],
        max_results: Optional[int] = None,
        domain_filter: Optional[List[str]] = None,
        language_filter: Optional[List[str]] = None,
    ):
        kwargs = {
            "query": query,
            "max_results": max_results or self.max_results,
            "max_tokens_per_page": self.max_tokens_per_page,
            "country": self.country,
        }
        if domain_filter:
            kwargs["search_domain_filter"] = domain_filter
        if language_filter:
            kwargs["search_language_filter"] = language_filter

        try:
            return self._client.search.create(**kwargs)
        except Exception as exc:
            self.logger.error(f"Perplexity search failed: {exc}")
            raise

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        domain_filter: Optional[List[str]] = None,
        language_filter: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Search the web via Perplexity. The caller crafts the query.

        Parameters:
            query: Any search query string.
            max_results: Override default result limit.
            domain_filter: Allowlist or denylist domains (prefix with '-' to exclude).
            language_filter: ISO 639-1 language codes, e.g. ["vi", "en"].

        Returns:
            List of result dicts with keys: title, url, snippet, date.
        """
        raw = self._call_api(query, max_results, domain_filter, language_filter)
        results = self._parse_results(raw.results)
        return SearchResponse(query=query, results=results).to_dict_list()

    def search_multi(
        self,
        queries: List[str],
        max_results_each: int = 5,
    ) -> List[dict]:
        """
        Execute up to 5 queries in one request.

        Parameters:
            queries: List of 1-5 query strings.
            max_results_each: Results per query.

        Returns:
            Flat list of all result dicts across queries.
        """
        if len(queries) > 5:
            raise ValueError("Perplexity multi-query supports at most 5 queries per request.")
        raw = self._call_api(queries, max_results=max_results_each)
        grouped = raw.results if hasattr(raw, "results") else []
        chunk = max(1, len(grouped) // max(len(queries), 1))
        all_results: List[dict] = []
        for i, q in enumerate(queries):
            slice_ = grouped[i * chunk : (i + 1) * chunk]
            results = self._parse_results(slice_)
            all_results.extend(SearchResponse(query=q, results=results).to_dict_list())
        return all_results
