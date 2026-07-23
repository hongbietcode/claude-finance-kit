"""SQLite state and idempotency storage for the monitor."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from claude_finance_kit.core.models import Bar, Signal
from claude_finance_kit.core.types import FeedHealth, MarketRegion


class MonitorStore:
    """Durable local state without persisting the raw all-market tick feed."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self._background_writes = 0
        self._last_background_commit = time.monotonic()
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS signals (
                dedupe_key TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                dedupe_key TEXT PRIMARY KEY,
                sent_at TEXT NOT NULL,
                channel TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notification_outbox (
                dedupe_key TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                text TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT,
                last_error_type TEXT,
                sent_at TEXT
            );
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                fees REAL NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paper_equity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cash REAL NOT NULL,
                position_value REAL NOT NULL,
                equity REAL NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS market_bars (
                market TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (market, symbol, timestamp)
            );
            CREATE INDEX IF NOT EXISTS market_bars_recent
                ON market_bars (market, symbol, timestamp DESC);
            CREATE TABLE IF NOT EXISTS checkpoints (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS health (
                source TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                last_event_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def _commit_background(self) -> None:
        self._background_writes += 1
        now = time.monotonic()
        if self._background_writes >= 100 or now - self._last_background_commit >= 1:
            self.connection.commit()
            self._background_writes = 0
            self._last_background_commit = now

    def signal_seen(self, dedupe_key: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM signals WHERE dedupe_key = ?",
            (dedupe_key,),
        ).fetchone()
        return row is not None

    def save_signal(self, dedupe_key: str, signal: Signal) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO signals VALUES (?, ?, ?, ?, ?)",
            (
                dedupe_key,
                signal.symbol,
                signal.action.value,
                signal.timestamp.isoformat(),
                signal.model_dump_json(),
            ),
        )
        self.connection.commit()

    def save_signal_state_and_notification(
        self,
        dedupe_key: str,
        signal: Signal,
        checkpoint_key: str,
        checkpoint_value: dict[str, Any],
        channel: str,
        text: str,
    ) -> None:
        """Atomically persist dedupe, pending paper state, and alert outbox."""

        now = datetime.now(UTC).isoformat()
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO signals VALUES (?, ?, ?, ?, ?)",
                (
                    dedupe_key,
                    signal.symbol,
                    signal.action.value,
                    signal.timestamp.isoformat(),
                    signal.model_dump_json(),
                ),
            )
            self.connection.execute(
                """
                INSERT INTO checkpoints VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value, updated_at=excluded.updated_at
                """,
                (checkpoint_key, json.dumps(checkpoint_value, default=str), now),
            )
            self.connection.execute(
                """
                INSERT OR IGNORE INTO notification_outbox
                (dedupe_key, channel, text, payload)
                VALUES (?, ?, ?, ?)
                """,
                (
                    dedupe_key,
                    channel,
                    text,
                    signal.model_dump_json(),
                ),
            )

    def alert_seen(self, dedupe_key: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM alerts WHERE dedupe_key = ?",
            (dedupe_key,),
        ).fetchone()
        return row is not None

    def save_alert(self, dedupe_key: str, channel: str, payload: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?)",
            (dedupe_key, datetime.now(UTC).isoformat(), channel, json.dumps(payload, default=str)),
        )
        self.connection.commit()

    def save_paper_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime,
        payload: dict[str, Any],
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO paper_trades
            (symbol, side, quantity, price, fees, timestamp, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                side,
                quantity,
                price,
                fees,
                timestamp.isoformat(),
                json.dumps(payload, default=str),
            ),
        )
        self.connection.commit()

    def save_paper_trade_and_checkpoint(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime,
        payload: dict[str, Any],
        checkpoint_key: str,
        checkpoint_value: dict[str, Any],
    ) -> None:
        """Atomically persist a paper fill with resulting cash/positions."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO paper_trades
                (symbol, side, quantity, price, fees, timestamp, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    side,
                    quantity,
                    price,
                    fees,
                    timestamp.isoformat(),
                    json.dumps(payload, default=str),
                ),
            )
            self.connection.execute(
                """
                INSERT INTO checkpoints VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value, updated_at=excluded.updated_at
                """,
                (
                    checkpoint_key,
                    json.dumps(checkpoint_value, default=str),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def checkpoint(self, key: str, value: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT INTO checkpoints VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, json.dumps(value, default=str), datetime.now(UTC).isoformat()),
        )
        self.connection.commit()

    def save_paper_equity(
        self,
        timestamp: datetime,
        cash: float,
        position_value: float,
        equity: float,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO paper_equity
            (timestamp, cash, position_value, equity, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp.isoformat(),
                cash,
                position_value,
                equity,
                json.dumps(payload or {}, default=str),
            ),
        )
        self._commit_background()

    def save_market_bar(self, bar: Bar, *, limit_per_symbol: int = 256) -> None:
        """Persist bounded completed aggregates, never raw market ticks."""

        self.connection.execute(
            """
            INSERT INTO market_bars VALUES (?, ?, ?, ?)
            ON CONFLICT(market, symbol, timestamp) DO UPDATE SET
                payload=excluded.payload
            """,
            (
                bar.market.value,
                bar.symbol,
                bar.timestamp.isoformat(),
                bar.model_dump_json(),
            ),
        )
        self.connection.execute(
            """
            DELETE FROM market_bars
            WHERE market=? AND symbol=? AND timestamp NOT IN (
                SELECT timestamp FROM market_bars
                WHERE market=? AND symbol=?
                ORDER BY timestamp DESC
                LIMIT ?
            )
            """,
            (
                bar.market.value,
                bar.symbol,
                bar.market.value,
                bar.symbol,
                limit_per_symbol,
            ),
        )
        self._commit_background()

    def load_market_bars(
        self,
        market: MarketRegion | str,
        symbols: list[str] | None = None,
        *,
        limit_per_symbol: int = 256,
    ) -> list[Bar]:
        """Restore recent per-symbol aggregates for restart-safe warmup."""

        market_value = MarketRegion(market).value
        parameters: list[Any] = [market_value]
        symbol_clause = ""
        if symbols:
            normalized = list(dict.fromkeys(symbol.upper() for symbol in symbols))
            placeholders = ", ".join("?" for _ in normalized)
            symbol_clause = f" AND symbol IN ({placeholders})"
            parameters.extend(normalized)
        rows = self.connection.execute(
            f"""
            SELECT payload FROM (
                SELECT payload, symbol, timestamp,
                       ROW_NUMBER() OVER (
                           PARTITION BY symbol ORDER BY timestamp DESC
                       ) AS rank
                FROM market_bars
                WHERE market=?{symbol_clause}
            )
            WHERE rank <= ?
            ORDER BY symbol, timestamp
            """,
            (*parameters, limit_per_symbol),
        ).fetchall()
        restored: list[Bar] = []
        for row in rows:
            try:
                restored.append(Bar.model_validate_json(row[0]))
            except (TypeError, ValueError):
                continue
        return restored

    def get_checkpoint(self, key: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT value FROM checkpoints WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(row[0])
        except (TypeError, ValueError):
            return None
        return value if isinstance(value, dict) else None

    def queue_notification(
        self,
        dedupe_key: str,
        channel: str,
        text: str,
        payload: dict[str, Any],
    ) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO notification_outbox
            (dedupe_key, channel, text, payload)
            VALUES (?, ?, ?, ?)
            """,
            (dedupe_key, channel, text, json.dumps(payload, default=str)),
        )
        self.connection.commit()

    def notification_seen(self, dedupe_key: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1 FROM notification_outbox WHERE dedupe_key = ?
            UNION SELECT 1 FROM alerts WHERE dedupe_key = ?
            LIMIT 1
            """,
            (dedupe_key, dedupe_key),
        ).fetchone()
        return row is not None

    def pending_notifications(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT dedupe_key, channel, text, payload, attempts, last_attempt_at
            FROM notification_outbox
            WHERE sent_at IS NULL
            ORDER BY attempts, rowid
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "dedupe_key": row[0],
                "channel": row[1],
                "text": row[2],
                "payload": json.loads(row[3]),
                "attempts": row[4],
                "last_attempt_at": row[5],
            }
            for row in rows
        ]

    def get_notification(self, dedupe_key: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            """
            SELECT dedupe_key, channel, text, payload, attempts, last_attempt_at
            FROM notification_outbox
            WHERE dedupe_key = ? AND sent_at IS NULL
            """,
            (dedupe_key,),
        ).fetchone()
        if row is None:
            return None
        return {
            "dedupe_key": row[0],
            "channel": row[1],
            "text": row[2],
            "payload": json.loads(row[3]),
            "attempts": row[4],
            "last_attempt_at": row[5],
        }

    def mark_notification_failed(self, dedupe_key: str, error_type: str) -> None:
        self.connection.execute(
            """
            UPDATE notification_outbox
            SET attempts=attempts + 1,
                last_attempt_at=?,
                last_error_type=?
            WHERE dedupe_key=?
            """,
            (datetime.now(UTC).isoformat(), error_type, dedupe_key),
        )
        self.connection.commit()

    def mark_notification_sent(
        self,
        dedupe_key: str,
        channel: str,
        payload: dict[str, Any],
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self.connection:
            self.connection.execute(
                """
                UPDATE notification_outbox
                SET sent_at=?, last_error_type=NULL
                WHERE dedupe_key=?
                """,
                (now, dedupe_key),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?)",
                (dedupe_key, now, channel, json.dumps(payload, default=str)),
            )

    def update_health(
        self,
        source: str,
        health: FeedHealth,
        metadata: dict[str, Any] | None = None,
        event_at: datetime | None = None,
    ) -> None:
        timestamp = event_at or datetime.now(UTC)
        self.connection.execute(
            """
            INSERT INTO health VALUES (?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                status=excluded.status,
                last_event_at=excluded.last_event_at,
                metadata=excluded.metadata
            """,
            (
                source.upper(),
                health.value,
                timestamp.isoformat(),
                json.dumps(metadata or {}, default=str),
            ),
        )
        self._commit_background()

    def get_health(self, source: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT status, last_event_at, metadata FROM health WHERE source = ?",
            (source.upper(),),
        ).fetchone()
        if not row:
            return None
        return {
            "status": row[0],
            "last_event_at": row[1],
            "metadata": json.loads(row[2]),
        }
