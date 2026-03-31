# Orchestration Protocol

Complexity-based routing for agent coordination. Match structure to task complexity — not uniform multi-agent for everything.

## Complexity Router

| Tier | Trigger Keywords | Structure | Agents | Rationale |
|------|-----------------|-----------|--------|-----------|
| T1 Simple | "price", "P/E of X", "current CPI", single metric | Single agent | 1 specialist | No synthesis needed, single data point |
| T2 Standard | "analyze TICKER", "deep dive", "technical analysis", "market briefing" | Parallel, no cross-talk | 2-3 specialists | Multi-perspective but independent sections |
| T3 Comparative | "compare", "buy/sell", "which is better", "screen + rank", "so sánh" | Hybrid: peers + leader | 2-3 specialists + lead-analyst | Needs synthesis to rank/decide |
| T4 Portfolio/Risk | "portfolio", "risk assessment", "sector rotation", "macro outlook + recommendation" | Vertical: leader + subordinates | lead-analyst + 2-3 specialists | Cross-domain risk synthesis |

## Communication Protocols

### T1: No Communication
- Single specialist agent runs analysis inline
- No orchestration overhead
- Expected quality: 4.5+ (highest for simple tasks)

### T2: Parallel, Independent
- 2-3 specialist agents run simultaneously
- Each produces its own section (fundamentals, technicals, news)
- Sections merged into report — no cross-referencing between agents
- Expected quality: 4.0+

### T3: Hybrid (Peers + Leader)
1. Specialist agents produce independent analyses (parallel)
2. lead-analyst receives all analyses
3. lead-analyst reviews for contradictions
4. lead-analyst issues final recommendation with confidence
- Expected quality: 3.8-4.0 with clear winner/ranking

### T4: Vertical (Leader + Subordinates)
1. lead-analyst breaks task into specific sub-assignments
2. Each specialist executes assigned task independently
3. Specialists cannot see each other's results (prevents herding)
4. lead-analyst collects all results sequentially
5. lead-analyst synthesizes, prioritizes risks, issues recommendation
- Expected quality: 3.8-3.9 with 66%+ decision accuracy

## Agent Roster

| Agent | Domain | T1 | T2 | T3 | T4 |
|-------|--------|----|----|----|----|
| fundamental-analyst | Valuation, financials, balance sheet | Solo | Parallel | Peer | Subordinate |
| technical-analyst | Trend, momentum, S/R, volume | Solo | Parallel | Peer | Subordinate |
| macro-researcher | GDP, CPI, rates, FX, commodities | Solo | Parallel | Peer | Subordinate |
| lead-analyst | Synthesis, decisions, risk ranking | — | — | Leader | Leader |

## Workflow → Tier Mapping

### stock-analysis skill
| Workflow | Tier | Agents |
|----------|------|--------|
| Single metric (P/E, price) | T1 | fundamental-analyst OR technical-analyst |
| Valuation / Health / Technical only | T1 | Relevant specialist |
| Stock Deep Dive ("analyze TICKER") | T2 | fundamental + technical + news parallel |
| Daily Market Briefing | T2 | macro + fundamental parallel |
| Screener (rank + compare) | T3 | fundamental + technical → lead-analyst ranks |
| Sector-specific (banking/RE/consumer) | T2 | fundamental-analyst with sector context |
| Portfolio Health Check | T4 | lead-analyst → fundamental + technical + macro |
| Macro Outlook + Sector Rotation | T4 | lead-analyst → macro + fundamental |

### market-research skill
| Workflow | Tier | Agents |
|----------|------|--------|
| Single metric (VNINDEX P/E, CPI) | T1 | macro-researcher |
| Market Briefing | T2 | macro + fundamental parallel |
| Sector Comparison + Rotation | T3 | macro + fundamental → lead-analyst |
| Full Macro Outlook + Portfolio Impact | T4 | lead-analyst → macro + fundamental + technical |

### news-sentiment skill
| Workflow | Tier | Agents |
|----------|------|--------|
| Headlines from specific site | T1 | Single crawler inline |
| News + sentiment for ticker/sector | T1 | Single agent (crawl + classify) |
| Comprehensive cross-site analysis | T2 | Parallel crawl by site, single classifier |

## Anti-Patterns

1. **Don't multi-agent simple queries** — Single agent scores 4.70, triple drops to 3.97
2. **Don't use horizontal consensus** — Round-robin debate creates hedge language, non-actionable output
3. **Don't skip lead-analyst in T3** — Without leader, contradictions go unresolved
4. **Don't let subordinates see each other in T4** — Causes herding toward first answer
5. **Don't use T4 for data retrieval** — Vertical overhead kills speed on simple tasks

## Forced Communication Milestones (T3 only)

When lead-analyst detects contradictions between specialists:
1. State the contradiction explicitly
2. Ask contradicting specialist to respond to opposing view (if time permits)
3. If no response: lead-analyst resolves using domain priority rules (see lead-analyst.md)

## References
- `agents/lead-analyst.md` — leader agent protocols
- `agents/fundamental-analyst.md`, `agents/technical-analyst.md`, `agents/macro-researcher.md` — specialist protocols
