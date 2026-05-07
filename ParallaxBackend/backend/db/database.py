from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS markets (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    slug TEXT,
                    category TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    closed INTEGER NOT NULL DEFAULT 0,
                    end_date TEXT,
                    liquidity REAL NOT NULL DEFAULT 0,
                    volume REAL NOT NULL DEFAULT 0,
                    image TEXT,
                    outcomes_json TEXT NOT NULL DEFAULT '[]',
                    outcome_prices_json TEXT NOT NULL DEFAULT '[]',
                    clob_token_ids_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL,
                    raw_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    yes_price REAL NOT NULL,
                    no_price REAL NOT NULL,
                    fair_probability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    liquidity REAL NOT NULL DEFAULT 0,
                    volume REAL NOT NULL DEFAULT 0,
                    raw_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (market_id) REFERENCES markets(id)
                );

                CREATE INDEX IF NOT EXISTS idx_market_snapshots_market_time
                    ON market_snapshots(market_id, captured_at);

                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    side TEXT NOT NULL,
                    market_price REAL NOT NULL,
                    fair_probability REAL NOT NULL,
                    edge REAL NOT NULL,
                    expected_value REAL NOT NULL,
                    confidence REAL NOT NULL,
                    max_stake REAL NOT NULL,
                    rationale TEXT NOT NULL,
                    FOREIGN KEY (market_id) REFERENCES markets(id)
                );

                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    initial_cash REAL NOT NULL,
                    cash_balance REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    realized_pnl REAL NOT NULL DEFAULT 0,
                    UNIQUE(portfolio_id, market_id, outcome),
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                    FOREIGN KEY (market_id) REFERENCES markets(id)
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    notional REAL NOT NULL,
                    fees REAL NOT NULL DEFAULT 0,
                    simulated_at TEXT NOT NULL,
                    strategy TEXT NOT NULL DEFAULT 'manual',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                    FOREIGN KEY (market_id) REFERENCES markets(id)
                );

                CREATE TABLE IF NOT EXISTS backtest_runs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    model_id TEXT,
                    initial_cash REAL NOT NULL,
                    final_equity REAL NOT NULL,
                    return_pct REAL NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    parameters_json TEXT NOT NULL DEFAULT '{}',
                    metrics_json TEXT NOT NULL DEFAULT '{}',
                    equity_curve_json TEXT NOT NULL DEFAULT '[]',
                    trades_json TEXT NOT NULL DEFAULT '[]'
                );
                """
            )
            self._ensure_column(conn, "backtest_runs", "model_id", "TEXT")

    @staticmethod
    def _loads(value: Optional[str], fallback: Any) -> Any:
        if not value:
            return fallback
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    @staticmethod
    def row_to_market(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item["active"] = bool(item.get("active"))
        item["closed"] = bool(item.get("closed"))
        item["outcomes"] = Database._loads(item.pop("outcomes_json", "[]"), [])
        item["outcome_prices"] = Database._loads(
            item.pop("outcome_prices_json", "[]"), []
        )
        item["clob_token_ids"] = Database._loads(
            item.pop("clob_token_ids_json", "[]"), []
        )
        item["raw"] = Database._loads(item.pop("raw_json", "{}"), {})
        return item

    @staticmethod
    def row_to_backtest(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item["parameters"] = Database._loads(item.pop("parameters_json", "{}"), {})
        item["metrics"] = Database._loads(item.pop("metrics_json", "{}"), {})
        item["equity_curve"] = Database._loads(item.pop("equity_curve_json", "[]"), [])
        item["trades"] = Database._loads(item.pop("trades_json", "[]"), [])
        return item

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if column not in {row["name"] for row in rows}:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def upsert_markets(self, markets: Iterable[Dict[str, Any]]) -> int:
        count = 0
        with self.connect() as conn:
            for market in markets:
                conn.execute(
                    """
                    INSERT INTO markets (
                        id, question, slug, category, active, closed, end_date,
                        liquidity, volume, image, outcomes_json, outcome_prices_json,
                        clob_token_ids_json, updated_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        question=excluded.question,
                        slug=excluded.slug,
                        category=excluded.category,
                        active=excluded.active,
                        closed=excluded.closed,
                        end_date=excluded.end_date,
                        liquidity=excluded.liquidity,
                        volume=excluded.volume,
                        image=excluded.image,
                        outcomes_json=excluded.outcomes_json,
                        outcome_prices_json=excluded.outcome_prices_json,
                        clob_token_ids_json=excluded.clob_token_ids_json,
                        updated_at=excluded.updated_at,
                        raw_json=excluded.raw_json
                    """,
                    (
                        market["id"],
                        market["question"],
                        market.get("slug", ""),
                        market.get("category", ""),
                        1 if market.get("active", True) else 0,
                        1 if market.get("closed", False) else 0,
                        market.get("end_date"),
                        float(market.get("liquidity") or 0),
                        float(market.get("volume") or 0),
                        market.get("image", ""),
                        json.dumps(market.get("outcomes", [])),
                        json.dumps(market.get("outcome_prices", [])),
                        json.dumps(market.get("clob_token_ids", [])),
                        market.get("updated_at") or utc_now(),
                        json.dumps(market.get("raw", {})),
                    ),
                )
                count += 1
        return count

    def list_markets(self, limit: int = 100, active_only: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM markets"
        params: List[Any] = []
        if active_only:
            query += " WHERE active = 1 AND closed = 0"
        query += " ORDER BY volume DESC, liquidity DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self.row_to_market(row) for row in rows]

    def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM markets WHERE id = ?", (market_id,)).fetchone()
        return self.row_to_market(row) if row else None

    def insert_snapshot(self, snapshot: Dict[str, Any]) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO market_snapshots (
                    market_id, captured_at, yes_price, no_price, fair_probability,
                    confidence, source, liquidity, volume, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot["market_id"],
                    snapshot.get("captured_at") or utc_now(),
                    snapshot["yes_price"],
                    snapshot["no_price"],
                    snapshot["fair_probability"],
                    snapshot["confidence"],
                    snapshot["source"],
                    snapshot.get("liquidity", 0),
                    snapshot.get("volume", 0),
                    json.dumps(snapshot.get("raw", {})),
                ),
            )
            return int(cursor.lastrowid)

    def list_snapshots(self, limit: int = 2000) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*, m.question, m.slug, m.category
                FROM market_snapshots s
                JOIN markets m ON m.id = s.market_id
                ORDER BY s.captured_at ASC, s.id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["raw"] = self._loads(item.pop("raw_json", "{}"), {})
            items.append(item)
        return items

    def replace_opportunities(self, opportunities: Iterable[Dict[str, Any]]) -> int:
        count = 0
        with self.connect() as conn:
            conn.execute("DELETE FROM opportunities")
            for opportunity in opportunities:
                conn.execute(
                    """
                    INSERT INTO opportunities (
                        market_id, detected_at, side, market_price, fair_probability,
                        edge, expected_value, confidence, max_stake, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        opportunity["market_id"],
                        opportunity.get("detected_at") or utc_now(),
                        opportunity["side"],
                        opportunity["market_price"],
                        opportunity["fair_probability"],
                        opportunity["edge"],
                        opportunity["expected_value"],
                        opportunity["confidence"],
                        opportunity["max_stake"],
                        opportunity["rationale"],
                    ),
                )
                count += 1
        return count

    def list_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT o.*, m.question, m.slug, m.category, m.liquidity, m.volume
                FROM opportunities o
                JOIN markets m ON m.id = o.market_id
                ORDER BY ABS(o.edge) DESC, o.confidence DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_portfolio(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO portfolios (id, name, initial_cash, cash_balance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    portfolio["id"],
                    portfolio["name"],
                    portfolio["initial_cash"],
                    portfolio["cash_balance"],
                    portfolio.get("created_at") or utc_now(),
                ),
            )
        return portfolio

    def list_portfolios(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            portfolios = conn.execute(
                "SELECT * FROM portfolios ORDER BY created_at DESC"
            ).fetchall()
            positions = conn.execute("SELECT * FROM positions").fetchall()
        position_map: Dict[str, List[Dict[str, Any]]] = {}
        for row in positions:
            position_map.setdefault(row["portfolio_id"], []).append(dict(row))
        result = []
        for row in portfolios:
            item = dict(row)
            item["positions"] = position_map.get(row["id"], [])
            result.append(item)
        return result

    def get_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM portfolios WHERE id = ?", (portfolio_id,)
            ).fetchone()
            if not row:
                return None
            positions = conn.execute(
                "SELECT * FROM positions WHERE portfolio_id = ?", (portfolio_id,)
            ).fetchall()
        item = dict(row)
        item["positions"] = [dict(position) for position in positions]
        return item

    def record_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            portfolio = conn.execute(
                "SELECT * FROM portfolios WHERE id = ?", (trade["portfolio_id"],)
            ).fetchone()
            if not portfolio:
                raise ValueError("Portfolio not found")

            side = trade["side"].upper()
            notional = float(trade["quantity"]) * float(trade["price"])
            fees = float(trade.get("fees", 0))
            cash_delta = -(notional + fees) if side == "BUY" else notional - fees
            new_cash = float(portfolio["cash_balance"]) + cash_delta
            if new_cash < -0.000001:
                raise ValueError("Insufficient simulated cash")

            position = conn.execute(
                """
                SELECT * FROM positions
                WHERE portfolio_id = ? AND market_id = ? AND outcome = ?
                """,
                (trade["portfolio_id"], trade["market_id"], trade["outcome"]),
            ).fetchone()

            quantity_delta = float(trade["quantity"]) if side == "BUY" else -float(trade["quantity"])
            if position:
                new_quantity = float(position["quantity"]) + quantity_delta
                if new_quantity < -0.000001:
                    raise ValueError("Cannot sell more simulated shares than the portfolio holds")
                if side == "BUY" and new_quantity > 0:
                    avg_price = (
                        (float(position["quantity"]) * float(position["avg_price"])) + notional
                    ) / new_quantity
                else:
                    avg_price = float(position["avg_price"]) if new_quantity > 0 else 0
                conn.execute(
                    """
                    UPDATE positions
                    SET quantity = ?, avg_price = ?
                    WHERE id = ?
                    """,
                    (new_quantity, avg_price, position["id"]),
                )
            else:
                if side == "SELL":
                    raise ValueError("Cannot sell a position that does not exist")
                conn.execute(
                    """
                    INSERT INTO positions (
                        portfolio_id, market_id, outcome, quantity, avg_price, realized_pnl
                    ) VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (
                        trade["portfolio_id"],
                        trade["market_id"],
                        trade["outcome"],
                        trade["quantity"],
                        trade["price"],
                    ),
                )

            conn.execute(
                "UPDATE portfolios SET cash_balance = ? WHERE id = ?",
                (new_cash, trade["portfolio_id"]),
            )
            cursor = conn.execute(
                """
                INSERT INTO trades (
                    portfolio_id, market_id, side, outcome, quantity, price,
                    notional, fees, simulated_at, strategy, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade["portfolio_id"],
                    trade["market_id"],
                    side,
                    trade["outcome"],
                    trade["quantity"],
                    trade["price"],
                    notional,
                    fees,
                    trade.get("simulated_at") or utc_now(),
                    trade.get("strategy", "manual"),
                    json.dumps(trade.get("metadata", {})),
                ),
            )
            trade["id"] = int(cursor.lastrowid)
            trade["notional"] = notional
            trade["fees"] = fees
            trade["side"] = side
        return trade

    def list_trades(self, portfolio_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        params: List[Any] = []
        query = "SELECT * FROM trades"
        if portfolio_id:
            query += " WHERE portfolio_id = ?"
            params.append(portfolio_id)
        query += " ORDER BY simulated_at DESC, id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = self._loads(item.pop("metadata_json", "{}"), {})
            result.append(item)
        return result

    def save_backtest(self, run: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO backtest_runs (
                    id, name, strategy, model_id, initial_cash, final_equity, return_pct,
                    started_at, completed_at, parameters_json, metrics_json,
                    equity_curve_json, trades_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["id"],
                    run["name"],
                    run["strategy"],
                    run.get("model_id"),
                    run["initial_cash"],
                    run["final_equity"],
                    run["return_pct"],
                    run["started_at"],
                    run["completed_at"],
                    json.dumps(run.get("parameters", {})),
                    json.dumps(run.get("metrics", {})),
                    json.dumps(run.get("equity_curve", [])),
                    json.dumps(run.get("trades", [])),
                ),
            )
        return run

    def list_backtests(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM backtest_runs ORDER BY completed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self.row_to_backtest(row) for row in rows]
