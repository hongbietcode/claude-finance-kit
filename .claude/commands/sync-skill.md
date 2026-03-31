Scan the claude-finance-kit codebase and sync all documentation files to match the actual code.

## What to scan

Source code at `src/claude_finance_kit/`:
- Public modules: `stock/`, `market/`, `macro/`, `fund/`, `commodity/`, `ta/`, `collector/`, `news/`, `search/`
- Internal: `_provider/`, `_internal/`, `core/`
- Top-level exports: `__init__.py` (`__all__` + `_LAZY_IMPORTS`)

Providers at `src/claude_finance_kit/_provider/`:
- Single-file: `vnd.py`, `mbk.py`, `spl.py`, `fmarket.py`
- Package: `vci/`, `kbs/`, `mas/`, `tvs/`, `vds/`, `fmp/`, `binance/`

## What to sync

For each module, extract: class names, public methods, method signatures (params + defaults), return types, docstrings.

### 1. `CLAUDE.md` — Project entry point
- Quick API Lookup table — must list every public facade + method
- Data Sources table — must match providers in `_provider/`
- Rules section — add gotchas for new modules
- Document Index — must list every `references/`, `docs/`, `skills/`, `agents/` file

### 2. `references/` — Detailed API docs
- `references/api-stock-and-company.md` ← from `stock/`, `_provider/vci/`, `_provider/kbs/`, `_provider/mas/`, `_provider/tvs/`, `_provider/vds/`, `_provider/fmp/`, `_provider/binance/`
- `references/api-market-macro-fund.md` ← from `market/`, `macro/`, `fund/`, `commodity/`
- `references/api-technical-analysis.md` ← from `ta/`
- `references/api-news-and-collector.md` ← from `news/`, `collector/`, `search/`
- `references/common-patterns.md` ← from `_internal/`, `core/exceptions.py`
- `references/analysis-methodology.md` ← keep as-is (domain knowledge, not code-derived)
- `references/html-report-styles.md` ← keep as-is (presentation, not code-derived)
- `references/claude-finance-kit-install-guide.md` ← verify extras match `pyproject.toml`

### 3. `docs/` — Module documentation
- `docs/README.md` ← package structure overview, reference file table
- `docs/01-getting-started.md` ← imports, quick start, optional modules, architecture tree
- `docs/02-stock-module.md` ← from `stock/` + provider implementations
- `docs/03-market-module.md` ← from `market/`
- `docs/04-macro-module.md` ← from `macro/`
- `docs/05-fund-module.md` ← from `fund/`
- `docs/06-commodity-module.md` ← from `commodity/`
- `docs/07-technical-analysis.md` ← from `ta/`
- `docs/09-collector-module.md` ← from `collector/`
- `docs/10-news-module.md` ← from `news/`
- `docs/11-advanced-topics.md` ← from `_provider/_registry.py`, `_internal/`, `core/`
- `docs/12-search-module.md` ← from `search/`

### 4. `skills/` — Skill files (check code examples still valid)
- `skills/stock-analysis/SKILL.md`
- `skills/market-research/SKILL.md`
- `skills/news-sentiment/SKILL.md`

## Process

1. Read `__init__.py` for every public module — get `__all__` and lazy imports
2. Read each module's classes and methods — extract signatures
3. Compare with existing docs — identify gaps (new methods, renamed params, removed APIs)
4. Update files IN PLACE — preserve structure, only change what's different
5. Verify imports: `python -c "from claude_finance_kit import Stock, Market, Macro, Fund, Commodity; from claude_finance_kit.search import PerplexitySearch"`
6. Report what changed vs what was already in sync

## Rules

- DO NOT invent APIs — only document what exists in code
- DO NOT change doc structure/formatting — only update content
- Preserve existing prose explanations and examples where still accurate
- If a method was removed from code, remove from docs
- If a method was added to code, add to docs in the appropriate section
- If a new module was added to code, create corresponding doc file
- Keep each doc file under 200 lines
