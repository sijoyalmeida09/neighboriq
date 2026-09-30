"""analysis_queue.py — Serial step runner with state persistence and progress display.

Runs the full business intelligence analysis in 10 sequential steps, saving JSON
state after each step so the analysis can resume if interrupted.

State file: .neighboriq/analysis_state.json (never committed — .gitignore: * is written there)
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["run_analysis", "get_report", "reset_analysis"]

# ── Step registry ─────────────────────────────────────────────────────────────

def _step_scan_repo(state: dict) -> dict:
    try:
        from neighboriq.intelligence.repo_scanner import scan_repo
        scan = scan_repo(state.get("root_path"))
        state["scan"] = dataclasses.asdict(scan)
        state["domain_id"] = scan.detected_domain or "local_service"
    except Exception as exc:
        state["errors"].append(f"scan_repo: {exc}")
    return state


def _step_classify(state: dict) -> dict:
    try:
        from neighboriq.intelligence.domain_taxonomy import get_domain
        domain = get_domain(state["domain_id"])
        state["naics_prefix"] = domain.naics_codes[0][:3] if domain.naics_codes else None
        state["domain_label"] = domain.label
    except Exception as exc:
        state["errors"].append(f"classify_domain: {exc}")
    return state


def _step_damodaran(state: dict) -> dict:
    try:
        from neighboriq.intelligence import benchmark_engine as be
        margins = be._fetch_damodaran_margins()
        keywords = be._DAMODARAN_KEYWORDS.get(state.get("domain_id", ""), [])
        for kw in keywords:
            result = be._find_damodaran_industry(kw, margins)
            if result:
                state["damodaran_match"] = {"industry": result[0], "margins": result[1]}
                break
    except Exception as exc:
        state["errors"].append(f"fetch_damodaran: {exc}")
    return state


def _step_susb(state: dict) -> dict:
    try:
        from neighboriq.intelligence import benchmark_engine as be
        naics = state.get("naics_prefix") or ""
        if naics:
            state["susb_data"] = be._fetch_census_susb(naics)
    except Exception as exc:
        state["errors"].append(f"fetch_susb: {exc}")
    return state


def _step_bls(state: dict) -> dict:
    try:
        from neighboriq.intelligence import benchmark_engine as be
        state["bls_wage"] = be._fetch_bls_avg_hourly_wage(state.get("domain_id", "local_service"))
    except Exception as exc:
        state["errors"].append(f"fetch_bls: {exc}")
        state["bls_wage"] = 18.0
    return state


def _step_fred(state: dict) -> dict:
    try:
        from neighboriq.intelligence import benchmark_engine as be
        state["fred_growth"] = be._fetch_fred_growth_rate(state.get("domain_id", "local_service"))
    except Exception as exc:
        state["errors"].append(f"fetch_fred: {exc}")
        state["fred_growth"] = 3.0
    return state


def _step_profile(state: dict) -> dict:
    try:
        from neighboriq.intelligence.auto_profiler import build_profile_from_scan
        from neighboriq.intelligence.repo_scanner import RepoScan
        from neighboriq.intelligence import benchmark_engine as be

        # Reconstruct RepoScan from stored dict
        scan_dict = state.get("scan", {})
        scan = _dict_to_dataclass(RepoScan, scan_dict)

        topup = state.get("topup", {})
        biz_name = topup.get("name") or scan_dict.get("readme_excerpt", "")[:40] or "My Business"
        profile = build_profile_from_scan(scan, topup, biz_name=biz_name)
        state["profile"] = dataclasses.asdict(profile)

        # Assemble DomainBenchmarks from accumulated step results
        benchmarks = be.get_benchmarks(
            state.get("domain_id", "local_service"),
            naics_prefix=state.get("naics_prefix"),
        )
        state["benchmarks"] = dataclasses.asdict(benchmarks)
    except Exception as exc:
        state["errors"].append(f"build_profile: {exc}")
    return state


def _step_verticals(state: dict) -> dict:
    try:
        from neighboriq.intelligence.vertical_finder import find_verticals, VerticalOpportunity
        from neighboriq.intelligence.benchmark_engine import DomainBenchmarks
        from neighboriq.intelligence.biz_profile import BizProfile

        profile = _dict_to_dataclass(BizProfile, state.get("profile", {}))
        benchmarks = _dict_to_dataclass(DomainBenchmarks, state.get("benchmarks", {}))
        domain_id = state.get("domain_id", "local_service")

        verticals = find_verticals(profile, benchmarks, domain_id, top_n=5)
        state["verticals"] = [dataclasses.asdict(v) for v in verticals]
    except Exception as exc:
        state["errors"].append(f"find_verticals: {exc}")
        state["verticals"] = []
    return state


def _step_roadmap(state: dict) -> dict:
    try:
        from neighboriq.intelligence.universal_roadmap import generate_roadmap
        from neighboriq.intelligence.domain_taxonomy import get_domain
        from neighboriq.intelligence.benchmark_engine import DomainBenchmarks
        from neighboriq.intelligence.biz_profile import BizProfile
        from neighboriq.intelligence.vertical_finder import VerticalOpportunity

        profile = _dict_to_dataclass(BizProfile, state.get("profile", {}))
        benchmarks = _dict_to_dataclass(DomainBenchmarks, state.get("benchmarks", {}))
        domain = get_domain(state.get("domain_id", "local_service"))
        verticals = tuple(
            _dict_to_dataclass(VerticalOpportunity, v)
            for v in state.get("verticals", [])
        )

        roadmap = generate_roadmap(profile, benchmarks, verticals, domain)
        state["roadmap"] = dataclasses.asdict(roadmap)
    except Exception as exc:
        state["errors"].append(f"generate_roadmap: {exc}")
    return state


def _step_format(state: dict) -> dict:
    try:
        from neighboriq.intelligence.universal_roadmap import format_roadmap, UniversalRoadmap
        roadmap = _dict_to_dataclass(UniversalRoadmap, state.get("roadmap", {}))
        state["formatted_report"] = format_roadmap(roadmap)
    except Exception as exc:
        state["errors"].append(f"format_output: {exc}")
        state["formatted_report"] = f"Analysis complete. Errors: {state.get('errors', [])}"
    return state


STEPS: list[tuple[str, str, object]] = [
    ("scan_repo",        "Scanning repository structure",      _step_scan_repo),
    ("classify_domain",  "Classifying business domain",        _step_classify),
    ("fetch_damodaran",  "Fetching industry margins (NYU)",    _step_damodaran),
    ("fetch_susb",       "Fetching Census revenue benchmarks", _step_susb),
    ("fetch_bls",        "Fetching BLS wage data",             _step_bls),
    ("fetch_fred",       "Fetching sector growth (FRED)",      _step_fred),
    ("build_profile",    "Building business profile",          _step_profile),
    ("find_verticals",   "Finding vertical opportunities",     _step_verticals),
    ("generate_roadmap", "Generating 3-phase roadmap",         _step_roadmap),
    ("format_output",    "Formatting final report",            _step_format),
]

# ── State persistence ─────────────────────────────────────────────────────────

def _state_path(root_path: str) -> Path:
    return Path(root_path) / ".neighboriq" / "analysis_state.json"


def _load_state(root_path: str) -> dict | None:
    path = _state_path(root_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        started = datetime.fromisoformat(data.get("started_at", "2000-01-01T00:00:00+00:00"))
        age_hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        if age_hours > 24:
            return None
        return data
    except Exception:
        return None


def _save_state(state: dict, root_path: str) -> None:
    try:
        path = _state_path(root_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        gitignore = path.parent / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*\n", encoding="utf-8")
        path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def _clear_state(root_path: str) -> None:
    try:
        _state_path(root_path).unlink(missing_ok=True)
    except Exception:
        pass


def _init_state(root_path: str) -> dict:
    return {
        "version": "1.0",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_steps": [],
        "current_step": None,
        "root_path": root_path,
        "domain_id": "local_service",
        "naics_prefix": None,
        "scan": {},
        "topup": {},
        "benchmarks": {},
        "profile": {},
        "verticals": [],
        "roadmap": {},
        "formatted_report": "",
        "errors": [],
    }

# ── Progress display ──────────────────────────────────────────────────────────

def _print_progress(step_num: int, total: int, label: str, status: str) -> None:
    filled = int((step_num / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    line = f"\r[{step_num}/{total}] {bar} {label}..."
    if status in ("done", "error", "skip"):
        suffix = " ✓" if status == "done" else (" ⟳" if status == "skip" else " ✗")
        sys.stdout.write(line + suffix + "\n")
    else:
        sys.stdout.write(line)
    sys.stdout.flush()

# ── Dataclass reconstruction helper ──────────────────────────────────────────

def _dict_to_dataclass(cls, data: dict):
    """Best-effort reconstruction of a frozen dataclass from a plain dict.
    Converts lists to tuples for tuple-typed fields. Skips unknown keys.
    """
    if not data:
        # Return a zeroed-out instance using dataclass defaults where possible
        fields = dataclasses.fields(cls)
        kwargs = {}
        for f in fields:
            origin = getattr(f.type, "__origin__", None)
            if f.type in (int, "int"):
                kwargs[f.name] = 0
            elif f.type in (float, "float"):
                kwargs[f.name] = 0.0
            elif f.type in (str, "str"):
                kwargs[f.name] = ""
            elif f.type in (bool, "bool"):
                kwargs[f.name] = False
            else:
                kwargs[f.name] = ()
        try:
            return cls(**kwargs)
        except Exception:
            return None

    fields = {f.name: f for f in dataclasses.fields(cls)}
    kwargs = {}
    for name, field in fields.items():
        val = data.get(name)
        if val is None:
            # Use a safe default
            raw_type = str(field.type)
            if "int" in raw_type:
                val = 0
            elif "float" in raw_type:
                val = 0.0
            elif "bool" in raw_type:
                val = False
            elif "str" in raw_type:
                val = ""
            else:
                val = ()
        elif isinstance(val, list):
            # Convert nested lists to tuples recursively
            val = _list_to_tuple(val)
        kwargs[name] = val
    try:
        return cls(**kwargs)
    except Exception:
        return None


def _list_to_tuple(val):
    if isinstance(val, list):
        return tuple(_list_to_tuple(i) for i in val)
    return val

# ── Main runner ───────────────────────────────────────────────────────────────

def run_analysis(
    root_path: str | None = None,
    topup: dict | None = None,
    resume: bool = True,
    force_restart: bool = False,
) -> dict:
    """Run all 10 analysis steps serially. Returns final state dict.

    Saves progress after each step to .neighboriq/analysis_state.json.
    Pass resume=True (default) to skip already-completed steps on re-run.
    Pass force_restart=True to ignore any existing state.
    """
    rp = root_path or os.getcwd()

    # Load or initialise state
    state: dict
    if force_restart:
        _clear_state(rp)
        state = _init_state(rp)
    elif resume:
        state = _load_state(rp) or _init_state(rp)
    else:
        state = _init_state(rp)

    state["root_path"] = rp
    if topup:
        state["topup"] = topup

    # If we need topup and don't have it, gather interactively after scan
    need_topup = not state.get("topup")

    total = len(STEPS)
    completed = set(state.get("completed_steps", []))

    for i, (step_id, label, fn) in enumerate(STEPS, start=1):
        if step_id in completed:
            _print_progress(i, total, label, "skip")
            continue

        _print_progress(i, total, label, "running")
        state["current_step"] = step_id

        # Special case: gather topup after scan if not yet provided
        if step_id == "build_profile" and need_topup and not state.get("topup"):
            try:
                from neighboriq.intelligence.repo_scanner import RepoScan, interactive_topup
                scan = _dict_to_dataclass(RepoScan, state.get("scan", {}))
                if scan:
                    gathered = interactive_topup(scan)
                    state["topup"] = gathered
                    need_topup = False
            except Exception as exc:
                state["errors"].append(f"interactive_topup: {exc}")

        state = fn(state)
        state.setdefault("completed_steps", [])
        if step_id not in state["completed_steps"]:
            state["completed_steps"].append(step_id)

        status = "error" if state["errors"] and state["errors"][-1].startswith(step_id) else "done"
        _print_progress(i, total, label, status)
        _save_state(state, rp)

    # Print final report
    report = state.get("formatted_report", "")
    if report:
        print("\n" + report)

    if state.get("errors"):
        print(f"\n⚠  {len(state['errors'])} non-fatal error(s) during analysis:")
        for e in state["errors"]:
            print(f"   • {e}")

    _clear_state(rp)
    return state


def get_report(root_path: str | None = None) -> str | None:
    """Return cached formatted_report if a completed analysis exists."""
    rp = root_path or os.getcwd()
    state = _load_state(rp)
    if state and state.get("formatted_report"):
        return state["formatted_report"]
    return None


def reset_analysis(root_path: str | None = None) -> None:
    """Delete state file — next run starts fresh."""
    _clear_state(root_path or os.getcwd())
    print("Analysis state cleared.")
