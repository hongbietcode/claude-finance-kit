---
date: 2026-07-22 15:57
severity: high
component: vnstock data backport
status: resolved
---

# Vnstock 4.0.3 Data Backport

## Context

This backport pulled Vnstock 3.5.1/4.0/4.0.3 data contracts into `claude-finance-kit` without breaking the existing `Stock` and `Market` facades. The real work was not the happy path; it was forcing the old GraphQL-driven code to survive REST-backed VCI, aligning KBS and VCI financial rows, and adding a public `Bond` facade without mutating existing behavior.

## What Happened

We shipped an additive `Bond` facade, public `InstrumentType`, expanded index recognition, MSN SecId resolution, source-safe HTTP fallback, REST VCI company/listing/finance, and normalized KBS/VCI period rows. Dependent scripts had to move with the schema change, especially the metric fetcher and screener, because the old ratio labels were no longer trustworthy.

Independent review mattered here. It found three real defects before I called this done: ETF symbols were being misclassified as warrants, KBS government-bond discovery was impossible because `FU_BOND` was not mapped, and `VCIFinancial` reused metadata too broadly and could drop later-symbol fields. Those findings changed the implementation. I tightened parser heuristics, made the bond facade explicitly surface the KBS limitation instead of pretending it worked, and keyed VCI metric maps by symbol.

## Reflection

The frustrating part is that a lot of the code looked correct until we compared actual outputs. The audit caught the bad assumptions: symbol length is not a type system, provider group codes drift, and cached metadata is not safe when a provider instance is reused. I also had to record the environment limitation for what it was: `.venv/bin/python -m pip install -U Codex-finance-kit` failed with `No matching distribution found for Codex-finance-kit`.

## Decisions

- Keep the `Bond` facade additive and leave `Stock`/`Market` signatures alone.
- Replace VCI GraphQL with REST endpoints and sanitize fallback URLs against an allowlist.
- Normalize both KBS and VCI to `symbol`, `year`, `period` rows, with `unit_multiplier` applied only to statement values.
- Treat KBS government-bond discovery as unsupported where the provider cannot answer it locally.
- Migrate the shipped scripts to the normalized ratio schema instead of preserving stale column labels.

## Next

Verification finished with focused regression coverage, full pytest, Ruff, and build/import smoke checks. The settled tree passes all `226` tests. Keep the regression tests that caught parser classification, bond capability handling, HTTP trust boundaries, import cycles, malformed provider responses, and VCI cache bugs. If this code moves again, start with provider contracts, not the scripts that consume them.
