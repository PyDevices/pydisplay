#!/usr/bin/env python3
"""
Run the sibling core pydevices timer probe on all desktop subprocess interpreters.

Always includes micropython.exe and python.exe from ~/bin (via example_interpreters.toml).

From repo root:
    python tools/run_test_timers.py
    ./tools/run_test_timers.py
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from example_test_kit import (  # noqa: E402
    compute_exit_code,
    example_timing,
    interpreter_timing_defaults,
    load_interpreters,
    load_manifest,
    print_table,
    run_case,
)

EXAMPLE_ID = "test_timers"


def _temp_dir() -> Path:
    return Path(
        os.environ.get("TEMP")
        or os.environ.get("TMPDIR")
        or os.environ.get("TMP")
        or tempfile.gettempdir()
    )


REPORT_PATH = _temp_dir() / "test_timers_report.md"

# Public probe labels in report column order.
PROBE_COLUMNS = (
    "machine.Timer",
    "AsyncTimer",
    "AsyncTimer (yield loop)",
    "multimer.auto.Timer",
)

# Desktop subprocess interpreters for timer probes (order matches typical dev setup).
DESKTOP_INTERPRETERS = (
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
    interpreters = [r["interpreter"] for r in rows]
    matrix: dict[str, dict[str, str]] = {}
    for row in rows:
        rt = row["interpreter"]
        stdout = row.get("stdout_tail") or ""
        matrix[rt] = _parse_probe_results(stdout)

    lines = [
        "# multimer timer probe report",
        "",
        f"Generated: {datetime.now(tz=UTC).date().isoformat()}  ",
        'Command: `export PATH="$HOME/bin:$PATH" && python tools/run_test_timers.py`',
        "",
        "Runs `pydevices/tools/test_timers.py` and probes public multimer APIs only (`Timer`, `AsyncTimer`, plus hardware `machine.Timer` when present).",
        "",
        "## Summary matrix",
        "",
        "| Timer backend | " + " | ".join(interpreters) + " |",
        "|---------------|" + "|".join(":-----------:" for _ in interpreters) + "|",
    ]
    for probe in PROBE_COLUMNS:
        cells = []
        for rt in interpreters:
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
            f"Raw JSON: `{_temp_dir() / 'test_timers_results.json'}`",
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
    interpreter_data = __import__("example_test_kit", fromlist=["load_toml"]).load_toml(
        REPO / "tools" / "example_interpreters.toml"
    )
    interpreter_defaults = interpreter_data.get("defaults", {})
    all_interpreters = load_interpreters()
    manifest_defaults, all_examples = load_manifest()

    example_meta = all_examples.get(EXAMPLE_ID)
    if example_meta is None:
        print(f"Example {EXAMPLE_ID!r} not in manifest", file=sys.stderr)
        return 2

    rows = []
    for interpreter_id in DESKTOP_INTERPRETERS:
        interpreter_meta = all_interpreters.get(interpreter_id)
        if interpreter_meta is None:
            print(f"Skipping {interpreter_id} (not in interpreters.toml)", file=sys.stderr)
            rows.append(
                {
                    "example": EXAMPLE_ID,
                    "interpreter": interpreter_id,
                    "summary": "missing",
                    "returncode": -1,
                    "timed_out": False,
                    "result": None,
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            )
            continue

        effective = interpreter_timing_defaults(interpreter_defaults, interpreter_meta)
        _duration, _timeout = example_timing(example_meta, manifest_defaults, effective)
        print(f"Running {EXAMPLE_ID} @ {interpreter_id}...", file=sys.stderr)
        rows.append(
            run_case(
                EXAMPLE_ID,
                example_meta,
                interpreter_id,
                interpreter_meta,
                manifest_defaults,
                interpreter_defaults,
            )
        )

    print()
    print_table(rows, "examples")

    out_path = _temp_dir() / "test_timers_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n")
    _write_report(rows)
    print(f"\nFull results: {out_path}", file=sys.stderr)
    print(f"Report: {REPORT_PATH}", file=sys.stderr)

    return compute_exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
