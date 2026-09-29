"""cache.py — Deterministic artifact cache for NeighborIQ.

Caches expensive API responses and LLM evaluations keyed by the inputs
that determine them. Prevents redundant spend on identical (zip, date)
lookups across runs.

Artifact types and default TTLs:
  - business_list   — scraped businesses for a zip (7 days)
  - market_eval     — LLM market analysis for a zip (3 days)
  - demand_signals  — Google Trends results (1 day)
  - demographics    — Census ACS data (30 days)

Hard rules:
  - stdlib only (hashlib, json, pathlib, datetime, os)
  - Atomic writes via temp-file + rename (works on NTFS and POSIX)
  - All I/O errors degrade to miss/no-op; NEVER raises
  - Stale entries (older than max_age_days) treated as cache miss
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("neighboriq.cache")

_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "artifact_cache"
_STATS_PATH = _CACHE_DIR / "_stats.json"

_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")

DEFAULT_TTL: dict[str, int] = {
    "business_list": 7,
    "market_eval": 3,
    "demand_signals": 1,
    "demographics": 30,
}


# ── normalization ──────────────────────────────────────────────────────────

def _norm_text(s: str | None) -> str:
    if not s:
        return ""
    return _WHITESPACE_RE.sub(" ", str(s).strip()).lower()


def schema_version() -> str:
    """Cache invalidator driven by NEIGHBORIQ_VERSION env var."""
    return os.environ.get("NEIGHBORIQ_VERSION", "v1")


# ── key derivation ─────────────────────────────────────────────────────────

def cache_key(
    artifact_type: str,
    *,
    zip_code: str = "",
    date_str: str = "",
    extra: str = "",
    version_override: str | None = None,
) -> str:
    """Deterministic 16-char hex key. Same inputs → same key, always."""
    sv = version_override or schema_version()
    components = "|".join([
        str(artifact_type),
        _norm_text(zip_code),
        _norm_text(date_str),
        _norm_text(extra),
        sv,
    ])
    return hashlib.sha1(components.encode("utf-8", errors="replace")).hexdigest()[:16]


# ── storage primitives ────────────────────────────────────────────────────

def _bucket_dir(artifact_type: str) -> Path:
    return _CACHE_DIR / artifact_type


def _entry_path(artifact_type: str, key: str) -> Path:
    return _bucket_dir(artifact_type) / f"{key}.json"


def _atomic_write_json(path: Path, payload: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        tmp.replace(path)
        return True
    except Exception as e:
        log.warning("[cache] atomic write failed %s: %s", path.name, e)
        return False


def _read_json(path: Path) -> Optional[dict]:
    try:
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return None
        return json.loads(raw)
    except Exception as e:
        log.warning("[cache] read failed %s: %s", path.name, e)
        return None


def _is_stale(entry: dict, max_age_days: int) -> bool:
    try:
        ts = entry.get("generated_at")
        if not ts:
            return True
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt
        return age > timedelta(days=max_age_days)
    except Exception:
        return True


# ── public API ─────────────────────────────────────────────────────────────

def get(artifact_type: str, key: str, max_age_days: int = 7) -> Optional[dict]:
    """Returns entry dict or None on miss / stale / invalid."""
    ttl = DEFAULT_TTL.get(artifact_type, max_age_days)
    entry = _read_json(_entry_path(artifact_type, key))
    if entry is None:
        _record_miss(artifact_type)
        return None
    if _is_stale(entry, ttl):
        _record_miss(artifact_type)
        return None
    _record_hit(artifact_type)
    return entry


def put(
    artifact_type: str,
    key: str,
    content: str,
    metadata: Optional[dict] = None,
    cost_usd: float = 0.0,
) -> bool:
    """Atomic write. Returns True on success, False on I/O failure."""
    payload = {
        "artifact_type": artifact_type,
        "key": key,
        "content": content or "",
        "metadata": dict(metadata or {}),
        "cost_usd": float(cost_usd),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return _atomic_write_json(_entry_path(artifact_type, key), payload)


def invalidate(artifact_type: str, key: str) -> bool:
    """Delete a specific cache entry. Returns True if deleted."""
    path = _entry_path(artifact_type, key)
    try:
        if path.exists():
            path.unlink()
            return True
    except Exception as e:
        log.warning("[cache] invalidate failed %s: %s", path.name, e)
    return False


def invalidate_zip(zip_code: str) -> int:
    """Delete all cached entries for a zip code. Returns count deleted."""
    if not zip_code:
        return 0
    target = _norm_text(zip_code)
    n = 0
    try:
        if not _CACHE_DIR.exists():
            return 0
        for bucket in _CACHE_DIR.iterdir():
            if not bucket.is_dir() or bucket.name.startswith("_"):
                continue
            for f in bucket.glob("*.json"):
                entry = _read_json(f)
                if not entry:
                    continue
                meta = entry.get("metadata") or {}
                if _norm_text(meta.get("zip_code") or "") == target:
                    try:
                        f.unlink()
                        n += 1
                    except Exception:
                        pass
    except Exception as e:
        log.warning("[cache] invalidate_zip failed: %s", e)
    return n


# ── stats ──────────────────────────────────────────────────────────────────

def _load_stats() -> dict:
    s = _read_json(_STATS_PATH) or {}
    s.setdefault("hits", {})
    s.setdefault("misses", {})
    return s


def _save_stats(s: dict) -> None:
    _atomic_write_json(_STATS_PATH, s)


def _record_hit(artifact_type: str) -> None:
    try:
        s = _load_stats()
        s["hits"][artifact_type] = int(s["hits"].get(artifact_type, 0)) + 1
        _save_stats(s)
    except Exception:
        pass


def _record_miss(artifact_type: str) -> None:
    try:
        s = _load_stats()
        s["misses"][artifact_type] = int(s["misses"].get(artifact_type, 0)) + 1
        _save_stats(s)
    except Exception:
        pass


def get_stats() -> dict:
    """Returns hit/miss counters + on-disk inventory."""
    s = _load_stats()
    inventory: dict[str, dict] = {}
    total_bytes = 0
    try:
        if _CACHE_DIR.exists():
            for bucket in sorted(_CACHE_DIR.iterdir()):
                if not bucket.is_dir() or bucket.name.startswith("_"):
                    continue
                files = list(bucket.glob("*.json"))
                size = sum(f.stat().st_size for f in files if f.is_file())
                inventory[bucket.name] = {"count": len(files), "bytes": size}
                total_bytes += size
    except Exception as e:
        log.warning("[cache] stats scan failed: %s", e)
    return {
        "hits": dict(s.get("hits", {})),
        "misses": dict(s.get("misses", {})),
        "inventory": inventory,
        "total_bytes": total_bytes,
        "schema_version": schema_version(),
    }
