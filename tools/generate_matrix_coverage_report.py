#!/usr/bin/env python3
"""Merge timer_async=0/1 matrix JSON into a markdown coverage report."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
CURSOR = REPO / ".cursor"


def load_rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [r for r in data if r]
    return [r for r in data.get("results", []) if r]


def classify(summary: str | None, result: dict | None) -> str:
    s = (summary or "").strip()
    if not s:
        return "unknown"
    if s == "hang" or "timed_out" in s.lower():
        return "hang"
    if s.startswith("matrix=false") or s.startswith("legacy") or s == "display_only":
        return "excluded"
    if "needs_playwright" in s or (result or {}).get("status") == "skip":
        return "skip"
    if "ok" in s and "error" not in s.lower():
        return "ok"
    if s.startswith("error") or (result or {}).get("status") == "error":
        return "error"
    if "exit_" in s or (result or {}).get("status") not in (None, "ok", "skip", "display_only"):
        # e.g. exit_1, exit_-11
        if "ok" in s:
            return "ok"
        return "fail"
    if "fail" in s.lower():
        return "fail"
    return "other:" + s[:40]


def main() -> int:
    paths = {
        "0": CURSOR / "example_test_results_timer_async_0.json",
        "1": CURSOR / "example_test_results_timer_async_1.json",
    }
    for p in paths.values():
        if not p.is_file():
            print(f"missing {p}", file=sys.stderr)
            return 1

    by_mode: dict[str, list[dict]] = {m: load_rows(p) for m, p in paths.items()}
    # (example, runtime) -> {mode: row}
    cells: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    runtimes = set()
    examples = set()
    for mode, rows in by_mode.items():
        for r in rows:
            ex, rt = r.get("example", "?"), r.get("runtime", "?")
            examples.add(ex)
            runtimes.add(rt)
            cells[(ex, rt)][mode] = r

    runtimes_sorted = sorted(runtimes)
    examples_sorted = sorted(examples)

    out = REPO / ".cursor" / "full_matrix_coverage_report.md"
    lines: list[str] = []
    lines.append("# Full example matrix coverage report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("**Harness:** `tools/example_test_kit.py --all-except-harness` on all 7 runtimes")
    lines.append(
        "**Modes:** `PYDISPLAY_TIMER_ASYNC=0` and `1` (14 concurrent jobs: runtime x mode)"
    )
    lines.append(
        "**Policy:** matrix/`skip_runtimes` exclusions cleared for this run; `kind=harness` still omitted."
    )
    lines.append("")
    lines.append(
        "Artifacts: `.cursor/example_test_results_rt_*_async_{0,1}.json` (shards), merged `.cursor/example_test_results_timer_async_{0,1}.json`"
    )
    lines.append("")

    # Summary counts per mode
    lines.append("## Summary counts")
    lines.append("")
    lines.append("| Mode | ok | fail | hang | skip | other | total cells |")
    lines.append("|------|---:|-----:|-----:|-----:|------:|------------:|")
    for mode in ("0", "1"):
        counts = defaultdict(int)
        for r in by_mode[mode]:
            counts[classify(r.get("summary"), r.get("result"))] += 1
        total = len(by_mode[mode])
        lines.append(
            f"| timer_async={mode} | {counts['ok']} | {counts['fail'] + counts['error']} | "
            f"{counts['hang']} | {counts['skip']} | "
            f"{sum(v for k, v in counts.items() if k not in ('ok', 'fail', 'error', 'hang', 'skip'))} | {total} |"
        )
    lines.append("")

    # Per-runtime rollup
    lines.append("## Per-runtime rollup")
    lines.append("")
    lines.append("| Runtime | mode0 ok | mode0 not-ok | mode1 ok | mode1 not-ok |")
    lines.append("|---------|---------:|-------------:|---------:|-------------:|")
    for rt in runtimes_sorted:
        c = {"0": defaultdict(int), "1": defaultdict(int)}
        for ex in examples_sorted:
            for mode in ("0", "1"):
                row = cells.get((ex, rt), {}).get(mode)
                if not row:
                    continue
                bucket = classify(row.get("summary"), row.get("result"))
                key = "ok" if bucket == "ok" else "not"
                c[mode][key] += 1
        lines.append(
            f"| `{rt}` | {c['0']['ok']} | {c['0']['not']} | {c['1']['ok']} | {c['1']['not']} |"
        )
    lines.append("")

    # Failures detail
    lines.append("## Non-ok cells (detail)")
    lines.append("")
    lines.append("| Example | Runtime | timer_async=0 | timer_async=1 | Notes |")
    lines.append("|---------|---------|---------------|---------------|-------|")
    for ex in examples_sorted:
        for rt in runtimes_sorted:
            pair = cells.get((ex, rt), {})
            if not pair:
                continue
            s0 = (
                classify(pair.get("0", {}).get("summary"), pair.get("0", {}).get("result"))
                if "0" in pair
                else "—"
            )
            s1 = (
                classify(pair.get("1", {}).get("summary"), pair.get("1", {}).get("result"))
                if "1" in pair
                else "—"
            )
            if s0 == "ok" and s1 == "ok":
                continue
            if s0 == "—" and s1 == "—":
                continue
            note_parts = []
            for mode, lab in (("0", s0), ("1", s1)):
                if lab in ("ok", "—"):
                    continue
                row = pair.get(mode, {})
                err = (row.get("result") or {}).get("error") or (row.get("stderr_tail") or "")[
                    :120
                ]
                if err:
                    note_parts.append(
                        f"m{mode}: {err.replace('|', '/').replace(chr(10), ' ')[:100]}"
                    )
            notes = "; ".join(note_parts) if note_parts else ""
            sum0 = pair.get("0", {}).get("summary", "—") if "0" in pair else "—"
            sum1 = pair.get("1", {}).get("summary", "—") if "1" in pair else "—"
            lines.append(f"| `{ex}` | `{rt}` | {sum0} | {sum1} | {notes} |")
    lines.append("")

    # Full grid (compact): example x runtime with 0/1
    lines.append("## Full grid (timer_async 0 / 1)")
    lines.append("")
    header = "| Example | " + " | ".join(runtimes_sorted) + " |"
    sep = "|---------|-" + "-|-".join(["------"] * len(runtimes_sorted)) + "-|"
    lines.append(header)
    lines.append(sep)
    for ex in examples_sorted:
        cols = []
        for rt in runtimes_sorted:
            pair = cells.get((ex, rt), {})
            a = (
                classify(pair.get("0", {}).get("summary"), pair.get("0", {}).get("result"))
                if "0" in pair
                else "—"
            )
            b = (
                classify(pair.get("1", {}).get("summary"), pair.get("1", {}).get("result"))
                if "1" in pair
                else "—"
            )

            def short(x):
                return {
                    "ok": "ok",
                    "hang": "hang",
                    "fail": "fail",
                    "error": "err",
                    "skip": "skip",
                }.get(x, x[:6])

            cols.append(f"{short(a)}/{short(b)}")
        lines.append(f"| `{ex}` | " + " | ".join(cols) + " |")
    lines.append("")

    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
