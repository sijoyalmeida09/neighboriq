"""
market_db.py
============
SQLite ORM for NeighborIQ. Stores neighborhoods, scraped businesses,
scored opportunities, and historical success patterns.

Database: data/market.db
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

log = logging.getLogger("market_db")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "market.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS neighborhoods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zip_code TEXT UNIQUE NOT NULL,
    city TEXT DEFAULT '',
    state TEXT DEFAULT '',
    lat REAL DEFAULT 0.0,
    lng REAL DEFAULT 0.0,
    population INTEGER DEFAULT 0,
    median_income INTEGER DEFAULT 0,
    age_median REAL DEFAULT 0.0,
    growth_rate_5yr REAL DEFAULT 0.0,
    last_analyzed TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    neighborhood_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    raw_category TEXT DEFAULT '',
    niche TEXT DEFAULT '',
    parent_category TEXT DEFAULT '',
    rating REAL DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    price_tier INTEGER DEFAULT 0,
    lat REAL DEFAULT 0.0,
    lng REAL DEFAULT 0.0,
    address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    source TEXT DEFAULT '',
    scraped_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    neighborhood_id INTEGER NOT NULL,
    niche TEXT NOT NULL,
    parent_category TEXT DEFAULT '',
    opportunity_score INTEGER DEFAULT 0,
    saturation_ratio REAL DEFAULT 0.0,
    demand_score INTEGER DEFAULT 0,
    competitor_avg_rating REAL DEFAULT 0.0,
    competitor_count INTEGER DEFAULT 0,
    pattern_confidence REAL DEFAULT 0.0,
    llm_analysis TEXT DEFAULT '',
    tier TEXT DEFAULT 'C',
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(neighborhood_id, niche),
    FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(id)
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demographic_profile_hash TEXT NOT NULL,
    city TEXT DEFAULT '',
    state TEXT DEFAULT '',
    niche TEXT NOT NULL,
    outcome TEXT NOT NULL,
    years_to_profit REAL DEFAULT 0.0,
    entry_capital_usd INTEGER DEFAULT 0,
    source TEXT DEFAULT 'manual',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_businesses_neighborhood ON businesses(neighborhood_id);
CREATE INDEX IF NOT EXISTS idx_businesses_niche ON businesses(niche);
CREATE INDEX IF NOT EXISTS idx_opportunities_neighborhood ON opportunities(neighborhood_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_tier ON opportunities(tier);
CREATE INDEX IF NOT EXISTS idx_patterns_hash_niche ON patterns(demographic_profile_hash, niche);
"""

_TIER_ORDER = {"A": 0, "B": 1, "C": 2}


class MarketDB:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self._path = Path(db_path) if db_path else DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)
        log.debug("market_db schema initialized at %s", self._path)

    # ── neighborhoods ──────────────────────────────────────────────────────

    def upsert_neighborhood(
        self,
        zip_code: str,
        city: str = "",
        state: str = "",
        lat: float = 0.0,
        lng: float = 0.0,
        population: int = 0,
        median_income: int = 0,
        age_median: float = 0.0,
        growth_rate_5yr: float = 0.0,
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO neighborhoods
                    (zip_code, city, state, lat, lng, population,
                     median_income, age_median, growth_rate_5yr, last_analyzed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(zip_code) DO UPDATE SET
                    city = excluded.city,
                    state = excluded.state,
                    lat = excluded.lat,
                    lng = excluded.lng,
                    population = excluded.population,
                    median_income = excluded.median_income,
                    age_median = excluded.age_median,
                    growth_rate_5yr = excluded.growth_rate_5yr,
                    last_analyzed = excluded.last_analyzed
                """,
                (
                    zip_code, city, state, lat, lng, population,
                    median_income, age_median, growth_rate_5yr,
                    datetime.utcnow().isoformat(),
                ),
            )
            row = conn.execute(
                "SELECT id FROM neighborhoods WHERE zip_code = ?", (zip_code,)
            ).fetchone()
            return int(row["id"])

    def get_neighborhood(self, zip_code: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM neighborhoods WHERE zip_code = ?", (zip_code,)
            ).fetchone()
            return dict(row) if row else None

    def neighborhood_exists(self, zip_code: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM neighborhoods WHERE zip_code = ?", (zip_code,)
            ).fetchone()
            return row is not None

    # ── businesses ────────────────────────────────────────────────────────

    def add_businesses(self, neighborhood_id: int, businesses: list[dict]) -> int:
        if not businesses:
            return 0
        rows = [
            (
                neighborhood_id,
                b.get("name", ""),
                b.get("raw_category", ""),
                b.get("niche", ""),
                b.get("parent_category", ""),
                float(b.get("rating", 0.0)),
                int(b.get("review_count", 0)),
                int(b.get("price_tier", 0)),
                float(b.get("lat", 0.0)),
                float(b.get("lng", 0.0)),
                b.get("address", ""),
                b.get("phone", ""),
                b.get("source", ""),
            )
            for b in businesses
        ]
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO businesses
                    (neighborhood_id, name, raw_category, niche, parent_category,
                     rating, review_count, price_tier, lat, lng, address, phone, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        log.info("Inserted %d businesses for neighborhood_id=%d", len(rows), neighborhood_id)
        return len(rows)

    def get_businesses(self, neighborhood_id: int) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM businesses WHERE neighborhood_id = ? ORDER BY rating DESC",
                (neighborhood_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── opportunities ──────────────────────────────────────────────────────

    def upsert_opportunity(
        self,
        neighborhood_id: int,
        niche: str,
        **fields: Any,
    ) -> int:
        allowed = {
            "parent_category", "opportunity_score", "saturation_ratio",
            "demand_score", "competitor_avg_rating", "competitor_count",
            "pattern_confidence", "llm_analysis", "tier",
        }
        safe = {k: v for k, v in fields.items() if k in allowed}
        safe.setdefault("tier", "C")

        set_clause = ", ".join(f"{k} = excluded.{k}" for k in safe)
        cols = ", ".join(["neighborhood_id", "niche"] + list(safe.keys()))
        placeholders = ", ".join(["?"] * (2 + len(safe)))

        with self._conn() as conn:
            conn.execute(
                f"""
                INSERT INTO opportunities ({cols})
                VALUES ({placeholders})
                ON CONFLICT(neighborhood_id, niche) DO UPDATE SET {set_clause}
                """,
                [neighborhood_id, niche] + list(safe.values()),
            )
            row = conn.execute(
                "SELECT id FROM opportunities WHERE neighborhood_id = ? AND niche = ?",
                (neighborhood_id, niche),
            ).fetchone()
            return int(row["id"])

    def get_opportunities(self, zip_code: str, min_tier: str = "C") -> list[dict]:
        tier_threshold = _TIER_ORDER.get(min_tier, 2)
        tiers = [t for t, rank in _TIER_ORDER.items() if rank <= tier_threshold]
        placeholders = ",".join("?" * len(tiers))
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT o.* FROM opportunities o
                JOIN neighborhoods n ON n.id = o.neighborhood_id
                WHERE n.zip_code = ? AND o.tier IN ({placeholders})
                ORDER BY o.opportunity_score DESC
                """,
                [zip_code] + tiers,
            ).fetchall()
            return [dict(r) for r in rows]

    # ── patterns ───────────────────────────────────────────────────────────

    def add_pattern(
        self,
        demographic_profile_hash: str,
        niche: str,
        outcome: str,
        **fields: Any,
    ) -> int:
        allowed = {
            "city", "state", "years_to_profit",
            "entry_capital_usd", "source", "notes",
        }
        safe = {k: v for k, v in fields.items() if k in allowed}
        cols = ", ".join(["demographic_profile_hash", "niche", "outcome"] + list(safe.keys()))
        placeholders = ", ".join(["?"] * (3 + len(safe)))
        with self._conn() as conn:
            cur = conn.execute(
                f"INSERT INTO patterns ({cols}) VALUES ({placeholders})",
                [demographic_profile_hash, niche, outcome] + list(safe.values()),
            )
            return int(cur.lastrowid)

    def get_patterns(self, demographic_profile_hash: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM patterns
                WHERE demographic_profile_hash = ?
                ORDER BY created_at DESC
                """,
                (demographic_profile_hash,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total_neighborhoods = conn.execute(
                "SELECT COUNT(*) FROM neighborhoods"
            ).fetchone()[0]
            total_businesses = conn.execute(
                "SELECT COUNT(*) FROM businesses"
            ).fetchone()[0]
            total_opportunities = conn.execute(
                "SELECT COUNT(*) FROM opportunities"
            ).fetchone()[0]
            tier_a_count = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE tier = 'A'"
            ).fetchone()[0]
        return {
            "total_neighborhoods": total_neighborhoods,
            "total_businesses": total_businesses,
            "total_opportunities": total_opportunities,
            "tier_a_count": tier_a_count,
        }
