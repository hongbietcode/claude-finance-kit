# Search Module

Web search via Perplexity API for aggregating stock, company, and market information.

## Requirements

- `pip install perplexityai`
- Set `PERPLEXITY_API_KEY` environment variable

## Quick Start

```python
from claude_finance_kit.search import PerplexitySearch

search = PerplexitySearch()
results = search.search("FPT earnings Q1 2025")
```

## Constructor

```python
PerplexitySearch(
    api_key=None,           # str | None — defaults to PERPLEXITY_API_KEY env var
    country="VN",           # str — ISO country code
    max_results=10,         # int — default result limit per query
    max_tokens_per_page=1024,  # int — max tokens per page in response
    debug=False,            # bool — enable debug logging
)
```

## Methods

### `search(query, max_results=None, domain_filter=None, language_filter=None) → List[dict]`

Search the web with a single query.

```python
results = search.search("FPT earnings Q1 2025")

results = search.search(
    "US Fed rate decision impact on Vietnam",
    max_results=5,
    domain_filter=["reuters.com", "bloomberg.com"],
    language_filter=["en"],
)
```

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str` | required | Any search query string |
| `max_results` | `int` | `None` | Override default limit |
| `domain_filter` | `List[str]` | `None` | Allowlist/denylist domains (prefix `-` to exclude) |
| `language_filter` | `List[str]` | `None` | ISO 639-1 codes, e.g. `["vi", "en"]` |

**Returns:** `List[dict]` with keys: `title`, `url`, `snippet`, `date`

### `search_multi(queries, max_results_each=5) → List[dict]`

Batch up to 5 queries in one API request.

```python
results = search.search_multi([
    "VN30 outlook 2025",
    "FPT vs VNM comparison",
    "kinh tế vĩ mô Việt Nam lãi suất 2025",
])
```

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `queries` | `List[str]` | required | 1–5 query strings |
| `max_results_each` | `int` | `5` | Results per query |

**Returns:** Flat `List[dict]` across all queries (same dict format as `search`)

## Data Models

```python
from claude_finance_kit.search.models import SearchResult, SearchResponse
```

| Model | Fields |
|-------|--------|
| `SearchResult` | `title: str`, `url: str`, `snippet: str`, `date: Optional[str]` |
| `SearchResponse` | `query: str`, `results: List[SearchResult]` |

Both have `.to_dict()` / `.to_dict_list()` methods.

## Gotchas

- `PERPLEXITY_API_KEY` env var required — raises `ValueError` if missing
- `perplexityai` package required — raises `ImportError` with install instructions if missing
- `search_multi` max 5 queries per request — raises `ValueError` if exceeded
- Default country is `"VN"` — change via `country` param for other regions
- Results are web search results, not stock data — the AI agent decides the query
