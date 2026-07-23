---
title: Documentation and release
status: completed
priority: P1
effort: medium
branch: main
tags: [docs, release]
created: 2026-07-23
---

# Phase 07: Documentation and release

Status: completed

Document provider coverage, US limitations, monitor setup, signal semantics,
backtest bias, and security. Synchronize package metadata at `0.2.0`, run all
quality gates, review public contracts, and prepare focused release changes.

## Requirements

- Update README, provider/stock/advanced/monitor docs, package metadata and
  static plugin manifests without adding agent workflows.
- Explain partial IEX, entitlement-dependent SSI, degraded polling,
  fail-closed validation, paper-only scope and environment-only secrets.
- Keep user-owned untracked paths outside the release commit.

## Files

- `README.md`, `docs/`, Python and npm package manifests.
- Plan/report artifacts under this work context.

## Validation

- Ruff, full pytest, package build/import, npm CLI build/smoke, docs links and
  Docker health smoke.
- Independent implementation review with all release blockers resolved.
- Focused conventional commit and push.

## Risk and rollback

Version metadata must move together. If a release gate fails, do not publish;
retain the focused commit locally until the failed contract is corrected.
