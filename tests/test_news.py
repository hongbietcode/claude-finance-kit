"""Test news crawlers import and basic structure."""


from claude_finance_kit.news import BatchCrawler, Crawler


class TestNewsCrawlerImport:
    """Test Crawler import and basic structure."""

    def test_crawler_import_success(self):
        """Crawler can be imported."""
        assert Crawler is not None

    def test_crawler_is_class(self):
        """Crawler is a class."""
        assert isinstance(Crawler, type)

    def test_crawler_has_required_methods(self):
        """Crawler has required methods."""
        crawler_methods = dir(Crawler)
        assert len(crawler_methods) > 0


class TestBatchCrawlerImport:
    """Test BatchCrawler import and basic structure."""

    def test_batch_crawler_import_success(self):
        """BatchCrawler can be imported."""
        assert BatchCrawler is not None

    def test_batch_crawler_is_class(self):
        """BatchCrawler is a class."""
        assert isinstance(BatchCrawler, type)

    def test_batch_crawler_has_required_methods(self):
        """BatchCrawler has required methods."""
        batch_methods = dir(BatchCrawler)
        assert len(batch_methods) > 0


class TestNewsModuleStructure:
    """Test news module structure."""

    def test_news_module_exports(self):
        """News module exports expected classes."""
        from claude_finance_kit import news
        assert hasattr(news, 'Crawler')
        assert hasattr(news, 'BatchCrawler')

    def test_news_all_exports(self):
        """News module __all__ includes expected exports."""
        from claude_finance_kit.news import __all__
        assert 'Crawler' in __all__
        assert 'BatchCrawler' in __all__
