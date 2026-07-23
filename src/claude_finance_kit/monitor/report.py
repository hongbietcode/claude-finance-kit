"""Self-contained monitor summary reports."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from html import escape
from pathlib import Path

from claude_finance_kit.core.models import Signal, UnusualFlowEvent


def write_daily_summary(
    output_dir: str | Path,
    report_date: date,
    signals: Iterable[Signal],
    flows: Iterable[UnusualFlowEvent],
) -> Path:
    output = Path(output_dir) / f"monitor-{report_date.isoformat()}-report.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    signal_rows = "".join(
        f"<tr><td>{escape(item.symbol)}</td><td>{item.action.value}</td><td>{item.confidence:.1f}</td>"
        f"<td>{item.regime.value}</td><td>{escape(', '.join(item.reasons))}</td></tr>"
        for item in signals
    )
    flow_rows = "".join(
        f"<tr><td>{escape(item.symbol)}</td><td>{item.direction}</td><td>{item.score:.1f}</td>"
        f"<td>{'yes' if item.confirmed else 'no'}</td></tr>"
        for item in flows
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Monitor summary {report_date.isoformat()}</title><style>
body{{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#172033}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #dde3ec;text-align:left}}
.note{{background:#eef6ff;padding:12px;border-radius:8px}}</style></head><body>
<h1>Market monitor — {report_date.isoformat()}</h1>
<p class="note">Research-only, paper-trade signals.
NO_TRADE is the safe default when validation or data is insufficient.</p>
<h2>Signals</h2><table><tr><th>Symbol</th><th>Action</th><th>Confidence</th><th>Regime</th><th>Reasons</th></tr>
{signal_rows or '<tr><td colspan="5">No signals</td></tr>'}</table>
<h2>Unusual flow</h2><table><tr><th>Symbol</th><th>Direction</th><th>Score</th><th>Confirmed</th></tr>
{flow_rows or '<tr><td colspan="4">No unusual flow events</td></tr>'}</table>
<p>Generated {datetime.now(UTC).isoformat()}</p></body></html>"""
    output.write_text(html, encoding="utf-8")
    return output
