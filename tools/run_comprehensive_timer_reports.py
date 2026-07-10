#!/usr/bin/env python3
"""
Run comprehensive multimer timer tests and write markdown reports.

Phase 1 — no LVGL: ``tools/test_timers.py`` on every desktop subprocess runtime.
Phase 2 — with LVGL: ``lv_test_timer.py kit`` x sync / async (via child env).

From repo root:
    python tools/run_comprehensive_timer_reports.py
    python tools/run_comprehensive_timer_reports.py --phase no-lvgl
    python tools/run_comprehensive_timer_reports.py --phase lvgl
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from example_test_kit import (  # noqa: E402
    example_timing,
    load_manifest,
    load_runtimes,
    run_case,
    runtime_timing_defaults,
)
from lv_timer_test_kit import (  # noqa: E402
    LVGL_RUNTIMES,
    MODES,
    parse_result,
)
from lv_timer_test_kit import (  # noqa: E402
    run_case as run_lvgl_case,
)
from run_test_timers import DESKTOP_RUNTIMES, PROBE_COLUMNS, _parse_probe_results  # noqa: E402

NO_LVGL_JSON = REPO / ".cursor" / "comprehensive_timers_no_lvgl_results.json"
LVGL_JSON = REPO / ".cursor" / "comprehensive_timers_lvgl_results.json"
NO_LVGL_REPORT = REPO / ".cursor" / "comprehensive_timers_no_lvgl_report.md"
LVGL_REPORT = REPO / ".cursor" / "comprehensive_timers_lvgl_report.md"

EXAMPLE_ID = "test_timers"

_PROBE_HEADER = re.compile(r"^([^\s].*):$")
_PROBE_STATUS = re.compile(r"^\s*(PASS|FAIL|SKIP)(?:\s*\(import\)|\s*\(runtime\))?:\s*(.*)$")
_PROBE_REASON = re.compile(r"^\s*reason:\s*(.*)$")


def _parse_probe_details(stdout: str) -> dict[str, dict]:
    """Full probe parse: status, detail, skip_reason."""
    out: dict[str, dict] = {}
    current: str | None = None
    for line in stdout.splitlines():
        m = _PROBE_HEADER.match(line)
        if m and not line.startswith(" "):
            current = m.group(1)
            out[current] = {
                "status": "?",
                "detail": "",
                "skip_reason": "",
            }
            continue
        if current is None:
            continue
        row = out[current]
        st = _PROBE_STATUS.match(line)
        if st:
            row["status"] = st.group(1)
            row["detail"] = st.group(2).strip()
            if st.group(1) == "SKIP" and "(import)" in line:
                row["status"] = "SKIP"
            continue
        if "SKIP (import)" in line or "SKIP (runtime)" in line:
            row["status"] = "SKIP"
            continue
        rm = _PROBE_REASON.match(line)
        if rm:
            row["skip_reason"] = rm.group(1).strip()
            continue

    # Merge simple matrix parser for any gaps
    simple = _parse_probe_results(stdout)
    for name, status in simple.items():
        if name not in out:
            out[name] = {"status": status, "detail": "", "skip_reason": ""}
        elif out[name]["status"] == "?" and status != "?":
            out[name]["status"] = status

    return out


def _platform_lines(stdout: str) -> list[str]:
    lines = []
    capture = False
    for line in stdout.splitlines():
        if line == "multimer timer probe":
            capture = True
            continue
        if capture:
            if not line.strip():
                break
            lines.append(line.strip())
    return lines


def run_no_lvgl_matrix() -> list[dict]:
    runtime_data = __import__("example_test_kit", fromlist=["load_toml"]).load_toml(
        REPO / "tools" / "example_runtimes.toml"
    )
    runtime_defaults = runtime_data.get("defaults", {})
    all_runtimes = load_runtimes()
    manifest_defaults, all_examples = load_manifest()
    example_meta = all_examples[EXAMPLE_ID]

    rows = []
    for runtime_id in DESKTOP_RUNTIMES:
        runtime_meta = all_runtimes.get(runtime_id)
        print(f"[no-lvgl] Running test_timers @ {runtime_id}...", file=sys.stderr)
        if runtime_meta is None:
            rows.append(
                {
                    "runtime": runtime_id,
                    "summary": "missing",
                    "timed_out": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "",
                    "probes": {},
                    "platform": [],
                }
            )
            continue
        row = run_case(
            EXAMPLE_ID,
            example_meta,
            runtime_id,
            runtime_meta,
            manifest_defaults,
            runtime_defaults,
        )
        stdout = row.get("stdout_tail") or ""
        rows.append(
            {
                "runtime": runtime_id,
                "summary": row.get("summary"),
                "timed_out": row.get("timed_out", False),
                "returncode": row.get("returncode"),
                "stdout": stdout,
                "stderr": row.get("stderr_tail") or "",
                "probes": _parse_probe_details(stdout),
                "platform": _platform_lines(stdout),
            }
        )
    return rows


def _lvgl_timeout(runtime_id: str) -> int:
    meta = load_runtimes().get(runtime_id, {})
    return int(meta.get("timeout_s", 45))


def run_lvgl_matrix() -> list[dict]:
    from lv_timer_test_kit import _resolve_command

    rows = []
    for runtime_id in LVGL_RUNTIMES:
        cmd = _resolve_command(runtime_id)
        for mode in MODES:
            print(f"[lvgl] Running {runtime_id} {mode}...", file=sys.stderr)
            if cmd is None:
                rows.append(
                    {
                        "runtime": runtime_id,
                        "mode": mode,
                        "summary": "missing",
                        "timed_out": False,
                        "returncode": -1,
                        "result": None,
                        "stdout": "",
                        "stderr": "",
                    }
                )
                continue
            timeout = _lvgl_timeout(runtime_id)
            row = run_lvgl_case(
                runtime_id,
                cmd,
                mode,
                timeout=timeout,
            )
            stdout = row.get("stdout_tail") or ""
            result = parse_result(stdout)
            rows.append(
                {
                    "runtime": runtime_id,
                    "mode": mode,
                    "summary": row.get("summary"),
                    "timed_out": row.get("timed_out", False),
                    "returncode": row.get("returncode"),
                    "result": result or row.get("result"),
                    "stdout": stdout,
                    "stderr": row.get("stderr_tail") or "",
                }
            )
    return rows


def _status_cell(status: str) -> str:
    if status == "PASS":
        return "**PASS**"
    if status == "FAIL":
        return "**FAIL**"
    if status == "SKIP":
        return "SKIP"
    if status == "missing":
        return "missing"
    return status or "?"


def write_no_lvgl_report(rows: list[dict]) -> None:
    runtimes = [r["runtime"] for r in rows]
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Comprehensive multimer timer report (no LVGL)",
        "",
        f"Generated: {now}  ",
        'Command: `export PATH="$HOME/bin:$PATH" && python tools/run_comprehensive_timer_reports.py --phase no-lvgl`',
        "",
        "Probes every importable ``multimer`` backend on each desktop runtime via ``tools/test_timers.py``.",
        "Import failures are reported as **SKIP** with reason (expected on wrong OS/port).",
        "",
        "## Summary matrix",
        "",
        "| Timer backend | " + " | ".join(runtimes) + " |",
        "|---------------|" + "|".join(":-----------:" for _ in runtimes) + "|",
    ]
    for probe in PROBE_COLUMNS:
        cells = []
        for row in rows:
            info = row.get("probes", {}).get(probe, {})
            cells.append(_status_cell(info.get("status", "?")))
        lines.append(f"| `{probe}` | " + " | ".join(cells) + " |")

    lines.extend(["", "## Per-runtime details", ""])
    for row in rows:
        rt = row["runtime"]
        lines.append(f"### `{rt}`")
        lines.append("")
        if row.get("summary") == "missing":
            lines.append("- **Runtime:** missing (executable not found)")
            lines.append("")
            continue
        if row.get("timed_out"):
            lines.append("- **Runner:** timed out")
        else:
            lines.append(f"- **Runner:** exit {row.get('returncode')}")
        for pl in row.get("platform") or []:
            lines.append(f"- {pl}")
        lines.append("")
        lines.append("| Probe | Result | Detail |")
        lines.append("|-------|--------|--------|")
        for probe in PROBE_COLUMNS:
            info = row.get("probes", {}).get(probe, {})
            status = info.get("status", "?")
            detail = info.get("detail") or info.get("skip_reason") or ""
            lines.append(f"| `{probe}` | {_status_cell(status)} | {detail} |")
        if row.get("stderr"):
            lines.extend(
                [
                    "",
                    "<details><summary>stderr</summary>",
                    "",
                    "```",
                    row["stderr"],
                    "```",
                    "</details>",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Legend",
            "",
            "- **PASS** — ≥2 callbacks in 300 ms",
            "- **FAIL** — ran but did not meet callback threshold or raised at runtime",
            "- **SKIP** — backend not importable on this port (with reason in detail)",
            "- **missing** — runtime executable not on PATH",
            "",
            f"Raw JSON: `{NO_LVGL_JSON.relative_to(REPO)}`",
            "",
        ]
    )
    NO_LVGL_REPORT.parent.mkdir(parents=True, exist_ok=True)
    NO_LVGL_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_lvgl_report(rows: list[dict]) -> None:
    runtimes = []
    seen = set()
    for row in rows:
        rt = row["runtime"]
        if rt not in seen:
            runtimes.append(rt)
            seen.add(rt)
    modes = list(MODES)
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Comprehensive LVGL timer report",
        "",
        f"Generated: {now}  ",
        'Command: `export PATH="$HOME/bin:$PATH" && python tools/run_comprehensive_timer_reports.py --phase lvgl`',
        "",
        "Runs ``examples/lv_test_timer.py kit`` (sync / async via ``PYDISPLAY_TIMER_ASYNC`` in the child env) on every desktop runtime.",
        "The example follows ``runtime.timer_async`` and does not set environment variables itself.",
        "",
        "## Summary matrix",
        "",
        f"| Runtime | {' | '.join(modes)} |",
        f"|---------|{'|'.join(':---------:' for _ in modes)}|",
    ]
    by_key = {(r["runtime"], r["mode"]): r for r in rows}
    for rt in runtimes:
        cells = [rt]
        for mode in modes:
            row = by_key.get((rt, mode))
            if row is None:
                cells.append("—")
            elif row.get("summary") == "missing":
                cells.append("missing")
            elif row.get("timed_out"):
                res = row.get("result") or {}
                backend = res.get("backend", "?")
                summary = row.get("summary", f"{backend}, hang")
                cells.append(summary)
            else:
                cells.append(row.get("summary", "?"))
        lines.append("| " + " | ".join(cells) + " |")

    lines.extend(["", "## Per-cell details", ""])
    for row in rows:
        rt, mode = row["runtime"], row["mode"]
        lines.append(f"### `{rt}` / `{mode}`")
        lines.append("")
        res = row.get("result")
        if row.get("summary") == "missing":
            lines.append("- **Status:** missing runtime")
        elif row.get("timed_out"):
            lines.append("- **Status:** subprocess timeout")
        else:
            lines.append(f"- **Summary:** {row.get('summary')}")
            lines.append(f"- **Exit code:** {row.get('returncode')}")
        if res:
            lines.append(f"- **KIT_RESULT:** `{json.dumps(res, separators=(',', ':'))}`")
        if row.get("stderr"):
            lines.extend(
                [
                    "",
                    "<details><summary>stderr</summary>",
                    "",
                    "```",
                    row["stderr"],
                    "```",
                    "</details>",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Legend",
            "",
            "- **ok** — timers ≥2 s and click checks passed",
            "- **hang** — subprocess timed out unexpectedly (often post-``KIT_RESULT`` quit teardown)",
            "- **missing** — runtime executable not on PATH",
            "",
            f"Raw JSON: `{LVGL_JSON.relative_to(REPO)}`",
            "",
        ]
    )
    LVGL_REPORT.parent.mkdir(parents=True, exist_ok=True)
    LVGL_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprehensive timer test reports")
    parser.add_argument(
        "--phase",
        choices=("all", "no-lvgl", "lvgl"),
        default="all",
        help="Which test phase to run (default: all)",
    )
    args = parser.parse_args()

    exit_code = 0

    if args.phase in ("all", "no-lvgl"):
        rows = run_no_lvgl_matrix()
        NO_LVGL_JSON.parent.mkdir(parents=True, exist_ok=True)
        NO_LVGL_JSON.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        write_no_lvgl_report(rows)
        print(f"\nNo-LVGL report: {NO_LVGL_REPORT}", file=sys.stderr)
        print(f"No-LVGL JSON:   {NO_LVGL_JSON}", file=sys.stderr)

    if args.phase in ("all", "lvgl"):
        rows = run_lvgl_matrix()
        LVGL_JSON.parent.mkdir(parents=True, exist_ok=True)
        LVGL_JSON.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        write_lvgl_report(rows)
        print(f"\nLVGL report: {LVGL_REPORT}", file=sys.stderr)
        print(f"LVGL JSON:   {LVGL_JSON}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
