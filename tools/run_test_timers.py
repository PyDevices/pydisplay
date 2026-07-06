#!/usr/bin/env python3
"""
Run tools/test_timers.py on all desktop subprocess runtimes.

Always includes micropython.exe and python.exe from ~/bin (via example_runtimes.toml).

From repo root:
    python tools/run_test_timers.py
    ./tools/run_test_timers.py
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from example_test_kit import (  # noqa: E402
    compute_exit_code,
    example_timing,
    load_manifest,
    load_runtimes,
    print_table,
    run_case,
    runtime_timing_defaults,
)

EXAMPLE_ID = "test_timers"
REPORT_PATH = REPO / "docs" / "testing" / "test_timers_report.md"

# Public probe labels in report column order.
PROBE_COLUMNS = (
    "machine.Timer",
    "AsyncTimer",
    "AsyncTimer (yield loop)",
    "multimer.Timer (default)",
)

# Desktop subprocess runtimes for timer probes (order matches typical dev setup).
DESKTOP_RUNTIMES = (
    "micropython",
    "micropython.exe",
    "circuitpython",
    "cpython-venv",
    "python.exe",
)


def _parse_probe_results(stdout: str) -> dict[str, str]:
    """Return probe label -> PASS / FAIL / SKIP / ? from test_timers stdout."""
    results: dict[str, str] = {}
    current: str | None = None
    for line in stdout.splitlines():
        if line.endswith(":") and not line.startswith(" "):
            current = line[:-1]
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("PASS:"):
            results[current] = "PASS"
            current = None
        elif stripped.startswith("FAIL"):
            results[current] = "FAIL"
            current = None
        elif stripped.startswith("SKIP"):
            results[current] = "SKIP"
            current = None
    return results


def _write_report(rows: list[dict]) -> None:
    runtimes = [r["runtime"] for r in rows]
    matrix: dict[str, dict[str, str]] = {}
    for row in rows:
        rt = row["runtime"]
        stdout = row.get("stdout_tail") or ""
        matrix[rt] = _parse_probe_results(stdout)

    lines = [
        "# multimer timer probe report",
        "",
        f"Generated: {datetime.now(tz=UTC).date().isoformat()}  ",
        'Command: `export PATH="$HOME/bin:$PATH" && python tools/run_test_timers.py`',
        "",
        "Probes public multimer APIs only (`Timer`, `AsyncTimer`, plus hardware `machine.Timer` when present).",
        "",
        "## Summary matrix",
        "",
        "| Timer backend | " + " | ".join(runtimes) + " |",
        "|---------------|" + "|".join(":-----------:" for _ in runtimes) + "|",
    ]
    for probe in PROBE_COLUMNS:
        cells = []
        for rt in runtimes:
            status = matrix.get(rt, {}).get(probe, "?")
            if status == "PASS":
                cells.append("**PASS**")
            elif status == "SKIP":
                cells.append("SKIP")
            elif status == "FAIL":
                cells.append("**FAIL**")
            else:
                cells.append("?")
        lines.append(f"| `{probe}` | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "**Legend:** **PASS** = ≥2 callbacks in 300 ms · **FAIL** = ran but failed · **SKIP** = not on this port",
            "",
            "Raw JSON: `.cursor/test_timers_results.json`",
            "",
            "## Reproduce",
            "",
            "```bash",
            'export PATH="$HOME/bin:$PATH"',
            "python tools/run_test_timers.py",
            "```",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    runtime_data = __import__("example_test_kit", fromlist=["load_toml"]).load_toml(
        REPO / "tools" / "example_runtimes.toml"
    )
    runtime_defaults = runtime_data.get("defaults", {})
    all_runtimes = load_runtimes()
    manifest_defaults, all_examples = load_manifest()

    example_meta = all_examples.get(EXAMPLE_ID)
    if example_meta is None:
        print(f"Example {EXAMPLE_ID!r} not in manifest", file=sys.stderr)
        return 2

    rows = []
    for runtime_id in DESKTOP_RUNTIMES:
        runtime_meta = all_runtimes.get(runtime_id)
        if runtime_meta is None:
            print(f"Skipping {runtime_id} (not in runtimes.toml)", file=sys.stderr)
            rows.append(
                {
                    "example": EXAMPLE_ID,
                    "runtime": runtime_id,
                    "summary": "missing",
                    "returncode": -1,
                    "timed_out": False,
                    "result": None,
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            )
            continue

        effective = runtime_timing_defaults(runtime_defaults, runtime_meta)
        _duration, _timeout = example_timing(example_meta, manifest_defaults, effective)
        print(f"Running {EXAMPLE_ID} @ {runtime_id}...", file=sys.stderr)
        rows.append(
            run_case(
                EXAMPLE_ID,
                example_meta,
                runtime_id,
                runtime_meta,
                manifest_defaults,
                runtime_defaults,
            )
        )

    print()
    print_table(rows, "examples")

    out_path = REPO / ".cursor" / "test_timers_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n")
    _write_report(rows)
    print(f"\nFull results: {out_path}", file=sys.stderr)
    print(f"Report: {REPORT_PATH}", file=sys.stderr)

    return compute_exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
