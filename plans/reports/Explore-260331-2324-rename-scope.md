# Scout Report: Full Renaming Scope (open-stock → claude-finance-kit)

**Date:** 2026-03-31  
**Project:** open-stock → claude-finance-kit  
**Explored Path:** /Users/huutri/code/clone/open-stock  
**Type:** Complete codebase analysis for renaming project  

---

## Executive Summary

This codebase requires comprehensive renaming across **140+ files** with **498 total pattern occurrences**. The project is a mature Python library (v0.1.7) with integrated Claude Code plugin, skills, and agents. Critical blocker is the primary package directory rename from `/src/open_stock/` to `/src/claude_finance_kit/`, which cascades to 105 Python files with imports.

**Estimated Effort:** High (systematic updates across all layers)  
**Risk Level:** Medium (straightforward text replacements; venv artifacts auto-regenerate)

---

## Project Context

| Attribute | Value |
|-----------|-------|
| **Project Name (Current)** | open-stock |
| **Project Name (Target)** | claude-finance-kit |
| **Python Package (Current)** | open_stock |
| **Python Package (Target)** | claude_finance_kit |
| **Version** | 0.1.7 |
| **License** | MIT (© 2026 open-stock contributors) |
| **Type** | Python library + Claude Code plugin |
| **Repo Root** | /Users/huutri/code/clone/open-stock |
| **Main Package** | /src/open_stock/ (→ /src/claude_finance_kit/) |

**Purpose:** Vietnamese stock market data & analysis library with unified interface for 15+ data sources (stock quotes, company info, technical analysis, macro data, news, mutual funds, batch collection).

---

## Pattern Analysis

### Pattern 1: "open-stock" (kebab-case)
**Total:** 80 occurrences across 36 files

| Category | Count | Files | Examples |
|----------|-------|-------|----------|
| Package metadata | 6 | pyproject.toml | `name = "open-stock"`, `[project.optional-dependencies] all = ["open-stock[..."]` |
| Documentation | 14 | README.md, docs/*, refs/* | Installation instructions, setup guides |
| Plugin/Config | 5 | .claude-plugin/plugin.json (3), Makefile (2) | Plugin name, zip artifacts |
| Build scripts | 2 | scripts/package-plugin.sh | Plugin packaging |
| Core modules | 4 | src/open_stock/core/*, __init__.py | Docstrings, error codes |
| License | 1 | LICENSE | Copyright notice |
| Agents/Skills | 7 | agents/*, skills/* | Self-descriptions |

**Files Affected:**
- pyproject.toml (6)
- README.md (13)
- CLAUDE.md (3)
- .claude-plugin/plugin.json (3)
- Makefile (2)
- scripts/package-plugin.sh (2)
- references/claude-finance-kit-install-guide.md (4)
- docs/01-getting-started.md (7)
- references/common-patterns.md (1)
- references/api-technical-analysis.md (1)
- references/api-news-and-collector.md (2)
- docs/09-collector-module.md (1)
- docs/10-news-module.md (2)
- src/open_stock/core/exceptions.py (2)
- src/open_stock/core/types.py (1)
- src/open_stock/core/models.py (1)
- src/open_stock/__init__.py (1)
- src/open_stock/_provider/{spl,fmarket,mbk,vnd}.py (4)
- agents/* (4)
- skills/* (5)
- LICENSE (1)
- requirements.txt (1)
- docs/README.md (3)

### Pattern 2: "open_stock" (snake_case)
**Total:** 393 occurrences across 105 files

| Category | Count | Files | Note |
|----------|-------|-------|------|
| **CRITICAL: Python imports** | ~350 | 105 files | All Python source files |
| Package path references | 43 | Various | `from open_stock.module import ...` patterns |

**Distribution:**
- Core modules: 17 main packages (stock, market, macro, fund, commodity, ta, news, collector, search, core, _internal, _provider)
- Provider implementations: ~30 files under _provider/
- Tests: 8 test files
- Documentation: 20+ doc files
- Config/command files: 4 files

**Blocking Issue:** Package directory `/src/open_stock/` must be renamed before any imports will work.

**Key Files with High Impact:**
- src/open_stock/__init__.py (10) - Main entry point, lazy imports
- src/open_stock/collector/__init__.py (10) - Batch collector
- src/open_stock/collector/tasks/ohlcv.py (7)
- src/open_stock/collector/tasks/intraday.py (8)
- src/open_stock/collector/tasks/financial.py (7)
- src/open_stock/_provider/kbs/__init__.py (7)
- src/open_stock/_provider/fmp/__init__.py (5)
- src/open_stock/_provider/mas/quote.py (5)
- src/open_stock/_provider/vci/quote.py (5)
- src/open_stock/_provider/kbs/quote.py (4)
- src/open_stock/_provider/fmp/company.py (3)
- src/open_stock/_provider/fmp/financial.py (3)
- src/open_stock/_provider/tvs/__init__.py (3)
- src/open_stock/_provider/tvs/company.py (4)
- src/open_stock/_provider/kbs/company.py (5)
- src/open_stock/_provider/vci/__init__.py (7)
- src/open_stock/_provider/vci/company.py (4)
- src/open_stock/_provider/vci/financial.py (3)
- src/open_stock/_provider/vci/listing.py (4)
- src/open_stock/_provider/vci/trading.py (3)
- Plus 85+ more with 1-3 occurrences each

### Pattern 3: "open stock" (space-separated)
**Total:** 0 occurrences

Not used in codebase.

### Pattern 4: "OpenStock" (PascalCase)
**Total:** 25 occurrences across 6 files

| File | Count | Context |
|------|-------|---------|
| src/open_stock/core/exceptions.py | 7 | Exception class definitions: OpenStockError (base), ProviderError, InvalidSymbolError, DataNotFoundError, RateLimitError, SourceNotAvailableError, InvalidDateRangeError |
| src/open_stock/core/__init__.py | 2 | Exports of exception classes |
| tests/test_imports.py | 2 | Import assertions |
| tests/test_core.py | 9 | Exception testing and assertions |
| docs/11-advanced-topics.md | 3 | Exception documentation |
| references/common-patterns.md | 2 | Usage examples |

**Critical Rename:** `OpenStockError` → `ClaudeFinanceKitError` (base exception class)

### Pattern 5: "openstock" (lowercase)
**Total:** 0 occurrences

Not used in codebase.

---

## Directory Structure Analysis

### Current Structure
```
/Users/huutri/code/clone/open-stock/
├── src/
│   └── open_stock/                    [MUST RENAME → claude_finance_kit]
│       ├── __init__.py                (1 docstring: "open-stock")
│       ├── core/
│       │   ├── __init__.py            (exports OpenStockError)
│       │   ├── exceptions.py          (7 OpenStockError references)
│       │   ├── types.py               (1 open-stock)
│       │   └── models.py              (1 open-stock)
│       ├── stock/                     (7 files, main facade)
│       │   ├── __init__.py            (7 open_stock imports)
│       │   ├── quote.py
│       │   ├── company.py
│       │   ├── financial.py
│       │   ├── listing.py
│       │   ├── trading.py
│       │   └── [6 more with open_stock imports]
│       ├── market/                    (2 open_stock imports)
│       ├── macro/                     (2 open_stock imports)
│       ├── fund/                      (2 open_stock imports)
│       ├── commodity/                 (2 open_stock imports)
│       ├── ta/                        (4 open_stock imports)
│       ├── technical_analysis/        (alternative path)
│       ├── news/                      (8 files, news crawling)
│       │   ├── __init__.py            (2 open_stock)
│       │   ├── core/
│       │   │   ├── crawler.py         (6 open_stock)
│       │   │   ├── batch.py           (2 open_stock)
│       │   │   └── [5 more]
│       │   └── config/
│       ├── collector/                 (10 files, batch collection)
│       │   ├── __init__.py            (10 open_stock)
│       │   ├── core/
│       │   │   ├── fetcher.py
│       │   │   ├── scheduler.py       (4 open_stock)
│       │   │   └── __init__.py        (5 open_stock)
│       │   ├── tasks/
│       │   │   ├── ohlcv.py           (7 open_stock)
│       │   │   ├── intraday.py        (8 open_stock)
│       │   │   ├── financial.py       (7 open_stock)
│       │   │   └── __init__.py        (4 open_stock)
│       │   └── stream/
│       ├── search/                    (2 open_stock imports)
│       ├── _provider/                 (~30 files, data providers)
│       │   ├── __init__.py            (2 open_stock)
│       │   ├── _registry.py           (2 open_stock)
│       │   ├── kbs/                   (5 files, 7 open_stock each)
│       │   ├── vci/                   (5 files, 7 open_stock each)
│       │   ├── mas/                   (4 files, 4 open_stock each)
│       │   ├── fmp/                   (5 files, 5 open_stock each)
│       │   ├── binance/               (3 files, 3 open_stock each)
│       │   ├── tvs/                   (3 files, 3 open_stock each)
│       │   ├── vds/                   (3 files, 3 open_stock each)
│       │   └── [spl, fmarket, mbk, vnd single files]
│       └── _internal/                 (8 files, utilities)
│           ├── __init__.py            (8 open_stock)
│           ├── env.py                 (2 open_stock)
│           ├── validation.py          (1 open_stock)
│           ├── transform.py           (2 open_stock)
│           ├── transform_ohlcv.py     (2 open_stock)
│           └── user_agent.py
├── tests/                             (8 test files)
├── docs/                              (14 doc files)
├── references/                        (6 reference guides)
├── agents/                            (4 agent definitions)
├── skills/                            (3 skill definitions)
├── .claude-plugin/
│   └── plugin.json                    (3 open-stock)
├── pyproject.toml                     (6 open-stock, 1 open_stock)
├── Makefile                           (2 open-stock)
├── LICENSE                            (1 open-stock)
├── README.md                          (13 open-stock)
├── CLAUDE.md                          (3 open-stock)
└── scripts/
    └── package-plugin.sh              (2 open-stock)
```

---

## Critical Path: Files That MUST Be Updated First

### 1. Primary Package Directory (BLOCKING)
**File:** `/src/open_stock/` → `/src/claude_finance_kit/`

**Why:** Every Python import statement depends on this. All 105 files with imports will fail until this is done.

**Scope:** Single directory rename (but requires update to pyproject.toml packages list)

### 2. Package Configuration
**File:** `pyproject.toml`

**Lines to update:**
- Line 6: `name = "open-stock"` → `name = "claude-finance-kit"`
- Line 70: `packages = ["src/open_stock"]` → `packages = ["src/claude_finance_kit"]`
- Line 56: `all = ["open-stock[ta,collector,news,search]"]` → `all = ["claude-finance-kit[ta,collector,news,search]"]`
- Lines 65-67: Project URLs (hostname references)

**Scope:** 6 occurrences, 1 file

### 3. Exception Base Class
**File:** `src/open_stock/core/exceptions.py` (after rename: `src/claude_finance_kit/core/exceptions.py`)

**Changes:**
- Class name: `OpenStockError` → `ClaudeFinanceKitError` (7 refs)
- Error code prefix: `OPEN_STOCK_` → `CLAUDE_FINANCE_KIT_` (in error_code defaults)
- Docstring: Update "open-stock" to "claude-finance-kit"

**Scope:** 7-10 changes, 1 file

**Cascade:** Updates needed in 5 more files (core/__init__.py, tests/test_core.py, tests/test_imports.py, docs/11-advanced-topics.md, references/common-patterns.md)

### 4. Core Module Exports
**File:** `src/open_stock/core/__init__.py` (after rename: `src/claude_finance_kit/core/__init__.py`)

**Changes:**
- Import path: `from open_stock.core.exceptions` → `from claude_finance_kit.core.exceptions`
- Export: `OpenStockError` → `ClaudeFinanceKitError`
- All exports in __all__ list

**Scope:** 2-4 changes, 1 file

### 5. Main Package Init
**File:** `src/open_stock/__init__.py` (after rename: `src/claude_finance_kit/__init__.py`)

**Changes:**
- Docstring: "open-stock: Vietnamese..." → "claude-finance-kit: Vietnamese..."
- Lazy imports: `"open_stock.stock"` → `"claude_finance_kit.stock"` (8 module paths)
- __module__ reference in __getattr__ (minor)

**Scope:** 10 changes, 1 file

---

## File-by-File Impact Matrix

### High Priority (Blocking or Critical)

| Priority | File | Changes | Type | Impact |
|----------|------|---------|------|--------|
| CRITICAL | src/open_stock/ → src/claude_finance_kit/ | Directory rename | Structure | All imports fail without this |
| CRITICAL | pyproject.toml | 6 | Config | Package metadata, build config |
| CRITICAL | src/open_stock/core/exceptions.py | 7 | Python | Exception definitions |
| CRITICAL | src/open_stock/__init__.py | 10 | Python | Main entry point, lazy imports |
| CRITICAL | All 105 Python files | ~393 | Python | Import statements |
| HIGH | .claude-plugin/plugin.json | 3 | Config | Plugin definition |
| HIGH | Makefile | 5 | Config | Build/release scripts |
| HIGH | All 8 test files | 40+ | Python | Import statements + asserts |
| HIGH | All 20+ doc files | 120+ | Markdown | Documentation examples |

### Medium Priority (Usability)

| File | Changes | Type | Impact |
|------|---------|------|--------|
| README.md | 13 | Markdown | User-facing documentation |
| references/claude-finance-kit-install-guide.md | 5 + filename | Markdown | Setup instructions |
| CLAUDE.md | 3 | Markdown | Plugin description |
| docs/01-getting-started.md | 7 | Markdown | Getting started guide |
| references/common-patterns.md | 13 (11 open_stock + 2 OpenStock) | Markdown | Code patterns |
| LICENSE | 1 | Text | Copyright (historical) |

### Low Priority (Cosmetic)

| File | Changes | Type | Impact |
|------|---------|------|--------|
| agents/* | 4 | Markdown | Agent descriptions |
| skills/* | 8 | Markdown | Skill descriptions |
| .claude/commands/sync-skill.md | 5 | Markdown | Internal command |
| requirements.txt | 1 | Text | Generated file |

---

## Implementation Roadmap

### Phase 1: Structure & Configuration (Enables Phase 2)
1. Rename directory: `/src/open_stock/` → `/src/claude_finance_kit/`
2. Update `pyproject.toml` (packages path + all name references)
3. Update `.claude-plugin/plugin.json` (plugin name)
4. Update `Makefile` (plugin artifact names)
5. **Test:** `python -c "from claude_finance_kit import Stock"` should fail with better error message

### Phase 2: Core Python Changes (Makes imports work)
1. Update exception class: `OpenStockError` → `ClaudeFinanceKitError` in core/exceptions.py
2. Update core module exports in core/__init__.py
3. Update main package init: src/claude_finance_kit/__init__.py (lazy imports)
4. Update all 105 Python files with imports (systematic find/replace)
5. Update all 8 test files with imports and assertions
6. **Test:** `python -m pytest tests/test_imports.py` should pass

### Phase 3: Documentation & Config (Makes it user-ready)
1. Update README.md (installation, examples, badges)
2. Update CLAUDE.md (plugin description)
3. Update all 20+ doc files (examples, import statements)
4. Update 6 reference files (install guide, patterns, API docs)
5. Update 4 agent/skill definition files
6. Update LICENSE copyright (optional: historical reference)
7. **Test:** `make requirements` to regenerate requirements.txt

### Phase 4: Verification & Build
1. Run: `pip install -e .` (generates new venv metadata)
2. Run: `python -m pytest tests/` (all imports should work)
3. Run: `make requirements` (exports updated requirements.txt)
4. Run: `make build` (generates wheel, sdist, plugin zip)
5. Verify all artifacts have new name: claude-finance-kit-*

---

## File Listing: Complete Change Matrix

### Configuration Files (4 files)

**pyproject.toml** (6 changes)
```
Line 6:   name = "open-stock"  →  "claude-finance-kit"
Line 8:   description = "Open-source Vietnamese..."  (update name)
Line 15:  keywords = [..., "open", "stock", ...]  (consider: finance, claude)
Line 56:  "open-stock[ta,...]"  →  "claude-finance-kit[ta,...]"
Line 65:  Homepage URL (if applicable)
Line 70:  packages = ["src/open_stock"]  →  ["src/claude_finance_kit"]
```

**.claude-plugin/plugin.json** (3 changes)
```
Line 2:   "name": "open-stock"  →  "claude-finance-kit"
Line 3:   description (update project name)
Line 6:   homepage URL (if applicable)
```

**Makefile** (5 changes)
```
Line 4:   Plugin variable uses "open-stock" pattern  →  "claude-finance-kit"
Lines 26,54: sed commands for version bumping
```

**scripts/package-plugin.sh** (2 changes)
```
Plugin zip filename references "open-stock"  →  "claude-finance-kit"
```

### Python Source Code (105 files)

**Core exception changes (1 file):**
- src/open_stock/core/exceptions.py → src/claude_finance_kit/core/exceptions.py
  - 7 × `OpenStockError` → `ClaudeFinanceKitError`
  - 1 × `OPEN_STOCK_000` → `CLAUDE_FINANCE_KIT_000`
  - 1 × error_code defaults

**Core module changes (1 file):**
- src/open_stock/core/__init__.py → src/claude_finance_kit/core/__init__.py
  - 2 × imports from open_stock.core.exceptions → claude_finance_kit.core.exceptions
  - 2 × OpenStockError → ClaudeFinanceKitError in __all__

**Main package changes (1 file):**
- src/open_stock/__init__.py → src/claude_finance_kit/__init__.py
  - 1 × docstring
  - 8 × lazy import module paths

**All remaining Python imports (101 files across 16 modules):**
```
from open_stock.stock import Stock          →  from claude_finance_kit.stock import Stock
from open_stock import Stock, Market, ...   →  from claude_finance_kit import ...
import open_stock                           →  import claude_finance_kit
from open_stock._provider import ...        →  from claude_finance_kit._provider import ...
```

### Documentation Files (20+ files)

**README.md** (13 changes)
- Installation: pip install open-stock → pip install claude-finance-kit
- Examples: from open_stock import → from claude_finance_kit import
- Project title/description
- Plugin commands: /open-stock:* → /claude-finance-kit:*

**CLAUDE.md** (3 changes)
- Project references
- Installation command
- Documentation references

**docs/01-getting-started.md** (7 changes)
- All import examples and installation commands

**docs/02-12** (20+ combined changes)
- Module documentation with import examples
- Technical references to module names

**references/claude-finance-kit-install-guide.md**
- FILENAME MUST CHANGE: claude-finance-kit-install-guide.md → claude-finance-kit-install-guide.md
- All content references (5 occurrences of "open-stock" + 1 open_stock)

**references/common-patterns.md** (13 changes)
- Code examples with imports
- 11 × open_stock, 2 × OpenStock

**Other reference files** (8 combined changes)
- api-technical-analysis.md, api-stock-and-company.md, api-market-macro-fund.md, api-news-and-collector.md

### Test Files (8 files)

**tests/test_imports.py** (8 changes)
- 6 × open_stock import statements
- 2 × OpenStockError assertions

**tests/test_core.py** (13 changes)
- 4 × open_stock imports
- 9 × OpenStockError references

**tests/test_stock_facade.py** (8 changes)
- All from open_stock.stock import

**tests/test_market_facade.py** (6 changes)

**tests/test_registry.py** (3 changes)

**tests/test_search.py** (11 changes)

**tests/test_news.py** (3 changes)

**tests/test_ta_indicators.py** (1 change)

### Other Configuration Files (3 files)

**LICENSE** (1 change)
- Copyright: "Copyright (c) 2026 open-stock contributors"

**.claude/commands/sync-skill.md** (5 changes)
- 2 × open-stock
- 3 × open_stock

**requirements.txt** (1 change)
- Generated file, update via `make requirements`

### Agent Definitions (4 files)

**agents/lead-analyst.md**, fundamental-analyst.md, technical-analyst.md, macro-researcher.md
- 4 combined changes (1 each)
- Update project references

### Skill Definitions (3 files)

**skills/stock-analysis/SKILL.md** (5-7 changes)
- Project references, usage examples

**skills/market-research/SKILL.md** (7 changes)

**skills/news-sentiment/SKILL.md** (3 changes)

---

## Virtual Environment & Build Artifacts

These files/directories will be **auto-regenerated** after `pip install -e .` and `make build`:

```
.venv/lib/python3.14/site-packages/
├── open_stock-0.1.7.dist-info/        [AUTO-REGENERATED as claude_finance_kit-*.dist-info]
│   ├── METADATA
│   ├── WHEEL
│   └── ...
└── _open_stock.pth                    [AUTO-REGENERATED as _claude_finance_kit.pth]

dist/
├── open-stock-plugin-v*.zip           [AUTO-REGENERATED]
├── open_stock-*.tar.gz                [AUTO-REGENERATED]
└── open_stock-*-py3-none-any.whl      [AUTO-REGENERATED]
```

**No manual changes needed for these.**

---

## Risk Assessment

### Low Risk
- Pure text replacements (kebab-case, snake_case)
- Documentation updates (won't break code)
- Configuration files (straightforward pattern matching)

### Medium Risk
- 105 Python files with imports (possibility of missed edge cases)
- Exception class renaming (need to ensure all references updated)
- Test files must pass after updates

### Mitigation
1. Use systematic find/replace with confirmation
2. Run full test suite after Phase 2: `python -m pytest tests/`
3. Run `pip install -e .` to verify package installation
4. Run `make build` to verify build artifacts
5. Check git diff before committing changes

---

## Success Criteria

✓ Package directory rename complete  
✓ All 105 Python files import correctly  
✓ All 8 test files pass (`pytest tests/`)  
✓ Package installs: `pip install -e .`  
✓ Build artifacts generated: `make build`  
✓ Documentation references updated (no broken examples)  
✓ Exception classes renamed and exported correctly  
✓ Plugin definition updated and correct  
✓ Git history clean with logical commits  

---

## Open Questions / Considerations

1. **Hostname rename:** Should GitHub URLs be updated to reflect new project name? (Currently references hongbietcode/open-stock)
2. **Keywords:** Should pyproject.toml keywords be updated? (Currently includes "vietnam", "stock", "finance")
3. **Copyright:** Update LICENSE to "© 2026 claude-finance-kit contributors" or keep historical?
4. **Version reset:** Keep 0.1.7 or reset to 0.1.0 for new name?
5. **Changelog:** Create migration guide for users updating from open-stock?

