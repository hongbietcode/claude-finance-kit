"""Tests for the Perplexity search module (import + structure only, no live API calls)."""

import pytest


class TestPerplexitySearchImport:
    def test_module_import(self):
        from claude_finance_kit.search import PerplexitySearch

        assert PerplexitySearch is not None

    def test_class_is_type(self):
        from claude_finance_kit.search import PerplexitySearch

        assert isinstance(PerplexitySearch, type)

    def test_lazy_import_from_root(self):
        import claude_finance_kit

        assert hasattr(claude_finance_kit, "PerplexitySearch") or "PerplexitySearch" in claude_finance_kit._LAZY_IMPORTS

    def test_search_module_all(self):
        from claude_finance_kit.search import __all__

        assert "PerplexitySearch" in __all__


class TestPerplexitySearchStructure:
    def setup_method(self):
        from claude_finance_kit.search import PerplexitySearch

        self.cls = PerplexitySearch

    def test_has_search_method(self):
        assert hasattr(self.cls, "search")

    def test_has_search_multi_method(self):
        assert hasattr(self.cls, "search_multi")

    def test_no_specialized_methods(self):
        for name in [
            "search_stock",
            "search_company",
            "search_market",
            "search_world_news",
            "search_macro",
            "search_vietnam_news",
        ]:
            assert not hasattr(self.cls, name), f"Specialized method {name} should not exist"


class TestPerplexitySearchInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        from claude_finance_kit.search import PerplexitySearch

        with pytest.raises(ValueError, match="PERPLEXITY_API_KEY"):
            PerplexitySearch()

    def test_raises_import_error_without_package(self, monkeypatch):
        import sys

        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")
        monkeypatch.setitem(sys.modules, "perplexity", None)
        from claude_finance_kit.search import PerplexitySearch

        with pytest.raises((ImportError, TypeError)):
            PerplexitySearch()


class TestSearchModels:
    def test_search_result_to_dict(self):
        from claude_finance_kit.search.models import SearchResult

        r = SearchResult(title="T", url="http://x.com", snippet="s", date="2025-01-01")
        d = r.to_dict()
        assert d["title"] == "T"
        assert d["url"] == "http://x.com"
        assert d["snippet"] == "s"
        assert d["date"] == "2025-01-01"

    def test_search_response_to_dict_list(self):
        from claude_finance_kit.search.models import SearchResponse, SearchResult

        r = SearchResult(title="T", url="http://x.com", snippet="s")
        resp = SearchResponse(query="test", results=[r])
        lst = resp.to_dict_list()
        assert len(lst) == 1
        assert lst[0]["title"] == "T"

    def test_search_result_optional_date(self):
        from claude_finance_kit.search.models import SearchResult

        r = SearchResult(title="T", url="u", snippet="s")
        assert r.date is None
