#!/usr/bin/env python3
"""
Cross-runtime example smoke test harness.

From repo root:
    python tools/example_test_kit.py
    python tools/example_test_kit.py --order runtimes
    python tools/example_test_kit.py --only-example calculator --only-runtime micropython
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from sibling_repos import apply_sibling_env
import tomllib

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
SRC = REPO / "src"
RUNTIMES_TOML = TOOLS / "example_runtimes.toml"
MANIFEST_TOML = TOOLS / "example_test_manifest.toml"
WRAPPER = TOOLS / "example_test_wrapper.py"
SERVE = TOOLS / "serve.py"
RESULT_RE = re.compile(r"^EXAMPLE_RESULT=(.+)$", re.MULTILINE)
DEFAULT_DURATION = 5
DEFAULT_TIMEOUT = 30
DEFAULT_ONESHOT_TIMEOUT = 15
PYSCRIPT_PORT = 8000
SUBPROCESS_RUNTIME_KIND = "subprocess"
RUNTIME_TIMING_KEYS = ("duration_s", "timeout_s", "oneshot_timeout_s")


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _split_list(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    out: list[str] = []
    for item in values:
        for part in item.split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out or None


def load_runtimes() -> dict[str, dict]:
    data = load_toml(RUNTIMES_TOML)
    return data.get("runtimes", {})


def load_manifest() -> tuple[dict, dict]:
    data = load_toml(MANIFEST_TOML)
    defaults = data.get("defaults", {})
    examples = data.get("examples", {})
    return defaults, examples


def _display_exclusion_label(meta: dict) -> str | None:
    """Label for examples shown in the matrix but not run by default."""
    if meta.get("kind") == "harness":
        return None
    parts: list[str] = []
    if meta.get("matrix") is False:
        parts.append("matrix=false")
    if meta.get("kind") == "legacy" and meta.get("quit") == "pending":
        parts.append("legacy/pending")
    return ", ".join(parts) if parts else None


def matrix_examples(
    examples: dict[str, dict],
    only: list[str] | None,
    *,
    all_except_harness: bool = False,
) -> dict[str, dict]:
    """Examples to execute. Harnesses are always excluded."""
    out = {}
    for name, meta in examples.items():
        if meta.get("kind") == "harness":
            continue
        if only and name not in only:
            continue
        if not all_except_harness and _display_exclusion_label(meta):
            continue
        out[name] = meta
    return out


def display_only_examples(
    examples: dict[str, dict],
    only: list[str] | None,
    *,
    all_except_harness: bool,
) -> dict[str, str]:
    """Examples listed in the matrix output but not executed (default mode only)."""
    if all_except_harness:
        return {}
    out: dict[str, str] = {}
    for name, meta in examples.items():
        if meta.get("kind") == "harness":
            continue
        if only and name not in only:
            continue
        label = _display_exclusion_label(meta)
        if label:
            out[name] = label
    return out


def append_display_rows(
    rows: list[dict],
    display_only: dict[str, str],
    runtimes: dict[str, dict],
    all_examples: dict[str, dict],
) -> list[dict]:
    """Add one row per (example, runtime) for manifest entries not run by default."""
    for example_id, label in sorted(display_only.items()):
        example_meta = all_examples[example_id]
        for runtime_id in sorted(runtimes):
            if not example_allowed_on_runtime(example_meta, runtime_id):
                continue
            rows.append(
                {
                    "example": example_id,
                    "runtime": runtime_id,
                    "summary": label,
                    "display_only": True,
                    "returncode": 0,
                    "timed_out": False,
                    "result": {"status": "display_only", "label": label},
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            )
    return rows


def _expand_user(path: str) -> str:
    return os.path.expanduser(path)


def resolve_runtime_exe(runtime_id: str, meta: dict) -> str | None:
    kind = meta.get("kind", SUBPROCESS_RUNTIME_KIND)
    if kind != SUBPROCESS_RUNTIME_KIND:
        return runtime_id

    command = meta.get("command", [])
    if not command:
        return None

    raw = command[0]
    if raw.startswith("repo:"):
        rel = raw.split(":", 1)[1]
        candidate = REPO / rel
        return str(candidate) if candidate.exists() else None

    if raw == ".venv/bin/python":
        candidate = REPO / ".venv" / "bin" / "python"
        return str(candidate) if candidate.exists() else None

    expanded = _expand_user(raw)
    if Path(expanded).exists():
        return expanded

    for rule in meta.get("resolve", []):
        if rule == "PATH":
            found = shutil.which(Path(raw).name)
            if found:
                return found
        elif rule.startswith("~/"):
            candidate = _expand_user(rule)
            if Path(candidate).exists():
                return candidate
        elif rule.startswith("repo:"):
            candidate = REPO / rule.split(":", 1)[1]
            if candidate.exists():
                return str(candidate)

    return shutil.which(Path(raw).name)


def runtime_available(runtime_id: str, meta: dict) -> bool:
    kind = meta.get("kind", SUBPROCESS_RUNTIME_KIND)
    if kind == SUBPROCESS_RUNTIME_KIND:
        return resolve_runtime_exe(runtime_id, meta) is not None
    if kind == "pyscript":
        return SERVE.exists()
    if kind == "jupyter":
        jupyter = REPO / ".venv" / "bin" / "jupyter"
        return jupyter.exists()
    return False


def example_allowed_on_runtime(example_meta: dict, runtime_id: str) -> bool:
    skip = example_meta.get("skip_runtimes", [])
    if runtime_id in skip:
        return False
    allowed = example_meta.get("runtimes")
    return not (allowed and runtime_id not in allowed and "*" not in allowed)


def parse_result(stdout: str) -> dict | None:
    for match in RESULT_RE.finditer(stdout):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def summarize(result: dict | None, returncode: int, timed_out: bool) -> str:
    if timed_out:
        return "hang"
    if result is None:
        return "no_result" if returncode == 0 else f"exit_{returncode}"
    status = result.get("status", "?")
    if status == "skip":
        return "skip"
    if status == "ok":
        backend = result.get("backend", "?")
        if backend == "headless":
            return "ok"
        return f"{backend}, ok"
    if status == "error":
        err = result.get("error", "error")
        return f"error: {err}"
    return status


def runtime_timing_defaults(global_defaults: dict, runtime_meta: dict) -> dict:
    """Merge per-runtime timing overrides from example_runtimes.toml."""
    merged = dict(global_defaults)
    for key in RUNTIME_TIMING_KEYS:
        if key in runtime_meta:
            merged[key] = runtime_meta[key]
    return merged


def example_timing(
    example_meta: dict, manifest_defaults: dict, runtime_defaults: dict
) -> tuple[float, float]:
    kind = example_meta.get("kind", "loop")
    duration = float(
        example_meta.get(
            "duration_s",
            runtime_defaults.get(
                "duration_s",
                manifest_defaults.get("duration_s", DEFAULT_DURATION),
            ),
        )
    )
    if kind == "oneshot":
        timeout = float(
            example_meta.get(
                "oneshot_timeout_s",
                example_meta.get(
                    "timeout_s",
                    runtime_defaults.get(
                        "oneshot_timeout_s",
                        manifest_defaults.get("oneshot_timeout_s", DEFAULT_ONESHOT_TIMEOUT),
                    ),
                ),
            )
        )
    else:
        timeout = float(
            example_meta.get(
                "timeout_s",
                runtime_defaults.get(
                    "timeout_s",
                    manifest_defaults.get("timeout_s", DEFAULT_TIMEOUT),
                ),
            )
        )
    return duration, timeout


def run_unit_tests() -> int:
    print("Running unit tests (python -m unittest discover -s tests)...", file=sys.stderr)
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=str(REPO),
        check=False,
    )
    return proc.returncode


def run_subprocess_case(
    runtime_id: str,
    exe: str,
    example_id: str,
    example_meta: dict,
    duration: float,
    timeout: float,
) -> dict:
    wrapper_rel = os.path.relpath(WRAPPER, SRC)
    script = example_meta.get("script", f"examples/{example_id}.py")
    kind = example_meta.get("kind", "loop")
    quit_mode = example_meta.get("quit", "poll")
    bootstrap = example_meta.get("bootstrap", "full")
    cmd = [
        exe,
        wrapper_rel,
        example_id,
        "--script",
        script,
        "--kind",
        kind,
        "--quit",
        quit_mode,
        "--bootstrap",
        bootstrap,
        "--duration",
        str(duration),
        "--timeout",
        str(timeout),
    ]
    env = os.environ.copy()
    apply_sibling_env(env, repo_root=str(REPO))
    # micropython.exe (Windows PE) cannot read WSL-exported env; pass via argv.
    timer_async = env.get("PYDISPLAY_TIMER_ASYNC")
    if timer_async is not None:
        cmd.extend(["--timer-async", str(timer_async)])
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(SRC),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 5,
            env=env,
            check=False,
        )
        timed_out = False
        returncode = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

    result = parse_result(stdout)
    summary = summarize(result, returncode, timed_out)
    return {
        "example": example_id,
        "runtime": runtime_id,
        "summary": summary,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_s": duration,
        "timeout_s": timeout,
        "result": result,
        "stdout_tail": stdout[-2000:] if stdout else "",
        "stderr_tail": stderr[-1000:] if stderr else "",
    }


_server_pid: int | None = None


def _server_ready(port: int = PYSCRIPT_PORT) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/web/pyscript/embed.html", timeout=2
        ) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError, ConnectionError):
        return False


PACKAGES_DIR = REPO / "packages"


def _pyscript_header_lists(script_path: Path) -> tuple[list[str], list[str], list[str]]:
    """Read ``# modules:`` / ``# manifests:`` / ``# deps:`` from an example (first 10 lines)."""
    modules: list[str] = []
    manifests: list[str] = []
    deps: list[str] = []
    if not script_path.is_file():
        return modules, manifests, deps
    try:
        with open(script_path, encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if i >= 10:
                    break
                s = line.strip()
                if s.startswith("# modules:"):
                    body = s.split(":", 1)[1].strip()
                    modules = [p.strip() for p in body.split(",") if p.strip()]
                elif s.startswith("# manifests:"):
                    body = s.split(":", 1)[1].strip()
                    manifests = [p.strip() for p in body.split(",") if p.strip()]
                elif s.startswith("# deps:"):
                    body = s.split(":", 1)[1].strip()
                    deps = [p.strip() for p in body.split(",") if p.strip()]
    except OSError:
        pass
    return modules, manifests, deps


def _pyscript_gallery_value(script_path: Path) -> str | None:
    """Return ``featured`` / ``skip`` / ``binaries`` from ``# gallery:``, or None."""
    if not script_path.is_file():
        return None
    try:
        with open(script_path, encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if i >= 10:
                    break
                s = line.strip()
                if s.startswith("# gallery:"):
                    body = s.split(":", 1)[1].strip().lower()
                    token = body.split(",")[0].strip()
                    return token or None
    except OSError:
        pass
    return None


def pyscript_skips_binaries(example_id: str, example_meta: dict) -> bool:
    """True when the example opts out of PyScript because mip cannot install binaries."""
    script = example_meta.get("script", f"examples/{example_id}.py")
    return _pyscript_gallery_value(SRC / script) == "binaries"


def pyscript_embed_query(example_id: str, example_meta: dict) -> str:
    """Build loader query via ``url_maker`` (modules/manifests/deps) for embed.html."""
    scripts_dir = str(REPO / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from url_maker import urls_from_deps

    script = example_meta.get("script", f"examples/{example_id}.py")
    script_path = SRC / script

    extra_modules, extra_manifests, deps = _pyscript_header_lists(script_path)

    modules: list[str] = []
    manifests: list[str] = []

    if (PACKAGES_DIR / f"{example_id}.json").is_file() and (
        SRC / "examples" / example_id
    ).is_dir():
        manifests = [example_id]
    elif script_path.is_file() and script_path.parent != SRC / "examples":
        pkg = script_path.parent.name
        if (PACKAGES_DIR / f"{pkg}.json").is_file() and (SRC / "examples" / pkg).is_dir():
            manifests = [pkg]
        else:
            modules = [example_id]
    else:
        modules = [example_id] + [m for m in extra_modules if m != example_id]

    for name in extra_modules:
        if name not in modules:
            modules.append(name)
    for name in extra_manifests:
        if name not in manifests:
            manifests.append(name)

    return urls_from_deps(
        modules=modules,
        manifests=manifests,
        deps=deps,
        runtime="micropython",
    ).lstrip("?")


def _kill_pyscript_port(port: int = PYSCRIPT_PORT) -> None:
    """Free ``port`` when a prior serve.py is wedged (listening but not HTTP-ready)."""
    global _server_pid
    if _server_pid is not None:
        try:
            os.kill(_server_pid, 9)
        except OSError:
            pass
        _server_pid = None
    # Best-effort: anything still bound to the port (stale kit / manual serve).
    subprocess.run(
        ["fuser", "-k", f"{port}/tcp"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.2)


def ensure_pyscript_server(port: int = PYSCRIPT_PORT) -> None:
    global _server_pid
    if _server_ready(port):
        return
    # Port may still be held by a dead/hung serve.py from an earlier case.
    _kill_pyscript_port(port)
    print(f"Starting {SERVE} on port {port}...", file=sys.stderr)
    # Access logs go to stderr; an unread PIPE fills (~64KiB) and deadlocks
    # ThreadingHTTPServer mid-matrix (HTML loads, MicroPython never starts).
    serve_log = REPO / ".cursor" / "pyscript_serve_kit.log"
    serve_log.parent.mkdir(parents=True, exist_ok=True)
    with open(serve_log, "ab") as log_fh:
        proc = subprocess.Popen(
            [sys.executable, str(SERVE), "-p", str(port)],
            cwd=str(REPO),
            stdout=subprocess.DEVNULL,
            stderr=log_fh,
        )
    _server_pid = proc.pid
    for _ in range(100):
        if _server_ready(port):
            return
        if proc.poll() is not None:
            try:
                err_tail = serve_log.read_bytes()[-500:].decode("utf-8", "replace")
            except OSError:
                err_tail = ""
            raise RuntimeError(
                f"PyScript server exited before ready on port {port}: {err_tail[-500:]}"
            )
        time.sleep(0.1)
    raise RuntimeError(f"PyScript server did not become ready on port {port}")


def run_pyscript_case(
    example_id: str,
    example_meta: dict,
    duration: float,
    timeout: float,
    port: int = PYSCRIPT_PORT,
) -> dict:
    if pyscript_skips_binaries(example_id, example_meta):
        result = {
            "runtime": "pyscript",
            "status": "skip",
            "example": example_id,
            "error": "skip: binaries (browser mip cannot install binary assets)",
        }
        return {
            "example": example_id,
            "runtime": "pyscript",
            "summary": "skip",
            "returncode": 0,
            "timed_out": False,
            "duration_s": duration,
            "timeout_s": timeout,
            "result": result,
            "stdout_tail": "EXAMPLE_RESULT=" + json.dumps(result, separators=(",", ":")),
            "stderr_tail": "",
        }

    ensure_pyscript_server(port)
    query = pyscript_embed_query(example_id, example_meta)
    url = f"http://127.0.0.1:{port}/web/pyscript/embed.html?{query}&autotest=1&duration={int(duration)}"

    try:
        from pyscript_autotest import run_autotest
    except ImportError:
        tools = str(TOOLS)
        if tools not in sys.path:
            sys.path.insert(0, tools)
        from pyscript_autotest import run_autotest

    try:
        result = run_autotest(url, duration_s=duration, timeout_s=timeout)
    except Exception as exc:
        return {
            "example": example_id,
            "runtime": "pyscript",
            "summary": f"error: {exc}",
            "returncode": 1,
            "timed_out": False,
            "duration_s": duration,
            "timeout_s": timeout,
            "result": {"status": "error", "error": str(exc)},
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }

    if result.get("status") == "skip" or result.get("error", "").startswith(
        "playwright not installed"
    ):
        return {
            "example": example_id,
            "runtime": "pyscript",
            "summary": "needs_playwright",
            "returncode": -1,
            "timed_out": False,
            "duration_s": duration,
            "timeout_s": timeout,
            "result": result,
            "stdout_tail": "",
            "stderr_tail": "",
        }

    summary = summarize(result, 0, False)
    line = "EXAMPLE_RESULT=" + json.dumps(result, separators=(",", ":"))
    return {
        "example": example_id,
        "runtime": "pyscript",
        "summary": summary,
        "returncode": 0 if result.get("status") == "ok" else 1,
        "timed_out": result.get("smoke") == "js_timeout",
        "duration_s": duration,
        "timeout_s": timeout,
        "result": result,
        "stdout_tail": line[-2000:],
        "stderr_tail": "\n".join((result.get("console_errors") or [])[:5])[-1000:],
    }


def _write_jupyter_notebook(example_id: str, example_meta: dict, duration_s: float) -> Path:
    import_line = f"import {example_meta.get('import', example_id)}"
    script = example_meta.get("script", f"examples/{example_id}.py")
    py = SRC / script
    if py.is_file() and "." in example_meta.get("import", ""):
        pkg = example_meta["import"].rsplit(".", 1)[0]
        if (SRC / "examples" / pkg / f"{pkg.split('.')[-1]}.py").exists():
            import_line = f"import {example_meta['import']}"

    tools_rel = os.path.relpath(TOOLS, SRC)
    test_mode_source = "\n".join(
        [
            "import sys",
            f"sys.path.insert(0, {tools_rel!r})",
            "import pydisplay_test_mode",
            "pydisplay_test_mode.ENABLED = True",
            f"pydisplay_test_mode.DURATION_S = {duration_s}",
            "pydisplay_test_mode.install_deadline_hook()",
            "",
        ]
    )

    cells = [
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": ["import lib.path\n"],
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [test_mode_source],
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [f"{import_line}\n"],
        },
    ]
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    # Unique path so concurrent matrix workers (runtime x timer_async) do not clobber.
    mode = os.environ.get("PYDISPLAY_TIMER_ASYNC", "x")
    out = SRC / f"run-{example_id}-async{mode}-{os.getpid()}.ipynb"
    out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    return out


def run_jupyter_case(
    example_id: str,
    example_meta: dict,
    duration: float,
    timeout: float,
) -> dict:
    venv_python = REPO / ".venv" / "bin" / "python"
    jupyter = REPO / ".venv" / "bin" / "jupyter"
    if not venv_python.exists() or not jupyter.exists():
        return {
            "example": example_id,
            "runtime": "jupyter",
            "summary": "missing",
            "returncode": -1,
            "timed_out": False,
            "duration_s": duration,
            "timeout_s": timeout,
            "result": None,
            "stdout_tail": "",
            "stderr_tail": "Jupyter venv not found",
        }

    nb_path = _write_jupyter_notebook(example_id, example_meta, duration)
    nbconvert_out = nb_path.with_name(f"{nb_path.stem}.nbconvert.ipynb")
    cmd = [
        str(jupyter),
        "nbconvert",
        "--execute",
        "--to",
        "notebook",
        "--ExecutePreprocessor.timeout={}".format(int(timeout)),
        "--ExecutePreprocessor.kernel_name=python3",
        str(nb_path),
    ]
    env = os.environ.copy()
    apply_sibling_env(env, repo_root=str(REPO), prepend_paths=[str(SRC)])

    try:
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(SRC),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout + 30,
                env=env,
                check=False,
            )
            timed_out = False
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            returncode = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = -1
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    finally:
        nbconvert_out.unlink(missing_ok=True)
        nb_path.unlink(missing_ok=True)

    ok = returncode == 0 and not timed_out
    result = {
        "example": example_id,
        "status": "ok" if ok else "error",
        "backend": "JNDisplay",
        "duration_s": duration,
    }
    if not ok:
        result["error"] = stderr[-200:] if stderr else f"exit_{returncode}"

    summary = summarize(result, returncode, timed_out)
    return {
        "example": example_id,
        "runtime": "jupyter",
        "summary": summary,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_s": duration,
        "timeout_s": timeout,
        "result": result,
        "stdout_tail": stdout[-2000:] if stdout else "",
        "stderr_tail": stderr[-1000:] if stderr else "",
    }


def run_case(
    example_id: str,
    example_meta: dict,
    runtime_id: str,
    runtime_meta: dict,
    manifest_defaults: dict,
    runtime_defaults: dict,
) -> dict:
    effective_defaults = runtime_timing_defaults(runtime_defaults, runtime_meta)
    duration, timeout = example_timing(example_meta, manifest_defaults, effective_defaults)
    kind = runtime_meta.get("kind", SUBPROCESS_RUNTIME_KIND)

    if kind == SUBPROCESS_RUNTIME_KIND:
        exe = resolve_runtime_exe(runtime_id, runtime_meta)
        if exe is None:
            return {
                "example": example_id,
                "runtime": runtime_id,
                "summary": "missing",
                "returncode": -1,
                "timed_out": False,
                "duration_s": duration,
                "timeout_s": timeout,
                "result": None,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        return run_subprocess_case(runtime_id, exe, example_id, example_meta, duration, timeout)

    if kind == "pyscript":
        return run_pyscript_case(example_id, example_meta, duration, timeout)

    if kind == "jupyter":
        return run_jupyter_case(example_id, example_meta, duration, timeout)

    return {
        "example": example_id,
        "runtime": runtime_id,
        "summary": "unsupported_runtime",
        "returncode": -1,
        "timed_out": False,
        "duration_s": duration,
        "timeout_s": timeout,
        "result": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }


def test_all_examples(
    examples: dict[str, dict],
    runtimes: dict[str, dict],
    manifest_defaults: dict,
    runtime_defaults: dict,
    *,
    fail_fast: bool = False,
    verbose: bool = False,
) -> list[dict]:
    rows = []
    for example_id, example_meta in examples.items():
        for runtime_id, runtime_meta in runtimes.items():
            if not example_allowed_on_runtime(example_meta, runtime_id):
                continue
            if not runtime_available(runtime_id, runtime_meta):
                if verbose:
                    print(
                        f"Skipping {example_id} @ {runtime_id} (runtime missing)", file=sys.stderr
                    )
                rows.append(
                    {
                        "example": example_id,
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
            print(f"Running {example_id} @ {runtime_id}...", file=sys.stderr)
            row = run_case(
                example_id,
                example_meta,
                runtime_id,
                runtime_meta,
                manifest_defaults,
                runtime_defaults,
            )
            rows.append(row)
            if fail_fast and _row_failed(row):
                break
    return rows


def _row_failed(row: dict) -> bool:
    if row.get("display_only"):
        return False
    if row["summary"] in ("missing", "skip", "needs_playwright"):
        return False
    if row["timed_out"]:
        return True
    if row["summary"].endswith(", ok"):
        return False
    result = row.get("result") or {}
    return result.get("status") != "ok"


def test_all_runtimes(
    examples: dict[str, dict],
    runtimes: dict[str, dict],
    manifest_defaults: dict,
    runtime_defaults: dict,
    *,
    fail_fast: bool = False,
    verbose: bool = False,
) -> list[dict]:
    rows = []
    for runtime_id, runtime_meta in runtimes.items():
        for example_id, example_meta in examples.items():
            if not example_allowed_on_runtime(example_meta, runtime_id):
                continue
            if not runtime_available(runtime_id, runtime_meta):
                if verbose:
                    print(
                        f"Skipping {example_id} @ {runtime_id} (runtime missing)", file=sys.stderr
                    )
                rows.append(
                    {
                        "example": example_id,
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
            print(f"Running {example_id} @ {runtime_id}...", file=sys.stderr)
            row = run_case(
                example_id,
                example_meta,
                runtime_id,
                runtime_meta,
                manifest_defaults,
                runtime_defaults,
            )
            rows.append(row)
            if fail_fast and _row_failed(row):
                break
    return rows


def print_table(rows: list[dict], order: str):
    if not rows:
        print("(no runs)")
        return

    if order == "examples":
        examples = sorted({r["example"] for r in rows})
        runtimes = sorted({r["runtime"] for r in rows})
        ex_w = max(10, max(len(e) for e in examples) + 2)
        rt_w = max(8, max(len(r) for r in runtimes) + 2)
        header = f"{'example':<{ex_w}} |" + "|".join(f"{rt:<{rt_w}}" for rt in runtimes)
        sep = "-" * ex_w + "-+-" + "-+-".join("-" * rt_w for _ in runtimes)
        print(header)
        print(sep)
        by_key = {(r["example"], r["runtime"]): r["summary"] for r in rows}
        for ex in examples:
            cells = [f"{ex:<{ex_w}}"]
            for rt in runtimes:
                cells.append(f"{by_key.get((ex, rt), '—'):<{rt_w}}")
            print(" |".join(cells))
    else:
        runtimes = sorted({r["runtime"] for r in rows})
        examples = sorted({r["example"] for r in rows})
        rt_w = max(12, max(len(r) for r in runtimes) + 2)
        ex_w = max(8, max(len(e) for e in examples) + 2)
        header = f"{'runtime':<{rt_w}} |" + "|".join(f"{ex:<{ex_w}}" for ex in examples)
        sep = "-" * rt_w + "-+-" + "-+-".join("-" * ex_w for _ in examples)
        print(header)
        print(sep)
        by_key = {(r["runtime"], r["example"]): r["summary"] for r in rows}
        for rt in runtimes:
            cells = [f"{rt:<{rt_w}}"]
            for ex in examples:
                cells.append(f"{by_key.get((rt, ex), '—'):<{ex_w}}")
            print(" |".join(cells))


def compute_exit_code(rows: list[dict]) -> int:
    for row in rows:
        if row.get("display_only"):
            continue
        if row["summary"] in ("missing", "skip", "needs_playwright"):
            continue
        if row["timed_out"]:
            return 1
        if row["summary"].endswith(", ok"):
            continue
        if row.get("result") and row["result"].get("status") == "ok":
            continue
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-runtime pydisplay example smoke tests")
    parser.add_argument(
        "--order",
        choices=("examples", "runtimes"),
        default="examples",
        help="examples: each example on all runtimes first; runtimes: each runtime on all examples first",
    )
    parser.add_argument("--only-example", nargs="+", help="Subset of example ids")
    parser.add_argument("--only-runtime", nargs="+", help="Subset of runtime ids")
    parser.add_argument(
        "--curated-only", action="store_true", help="Run only the v1 curated examples"
    )
    parser.add_argument(
        "--all-except-harness",
        action="store_true",
        help="Run every manifest example except kind=harness (includes matrix=false and legacy/pending)",
    )
    parser.add_argument("--no-unit-tests", action="store_true", help="Skip unittest gate")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print full JSON rows to stdout")
    parser.add_argument(
        "--results-json",
        metavar="PATH",
        help="Write full result rows to PATH (default: .cursor/example_test_results.json)",
    )
    parser.add_argument(
        "--duration-s",
        type=float,
        metavar="SEC",
        help="Override per-example duration_s (quit inject / test-mode wall clock)",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        metavar="SEC",
        help="Override per-example timeout_s (and oneshot_timeout_s)",
    )
    args = parser.parse_args(argv)

    if not args.no_unit_tests:
        rc = run_unit_tests()
        if rc != 0:
            print("Unit tests failed; aborting example matrix.", file=sys.stderr)
            return rc

    runtime_data = load_toml(RUNTIMES_TOML)
    runtime_defaults = runtime_data.get("defaults", {})
    if args.duration_s is not None:
        runtime_defaults["duration_s"] = args.duration_s
    if args.timeout_s is not None:
        runtime_defaults["timeout_s"] = args.timeout_s
        runtime_defaults["oneshot_timeout_s"] = args.timeout_s
    runtimes = load_runtimes()
    manifest_defaults, all_examples = load_manifest()

    # CLI timing overrides also win over per-example manifest values.
    if args.duration_s is not None or args.timeout_s is not None:
        for meta in all_examples.values():
            if args.duration_s is not None:
                meta["duration_s"] = args.duration_s
            if args.timeout_s is not None:
                meta["timeout_s"] = args.timeout_s
                meta["oneshot_timeout_s"] = args.timeout_s

    if args.only_runtime:
        only_rt = _split_list(args.only_runtime)
        runtimes = {k: v for k, v in runtimes.items() if k in only_rt}

    only_examples = _split_list(args.only_example)
    examples = matrix_examples(
        all_examples, only_examples, all_except_harness=args.all_except_harness
    )
    display_only = display_only_examples(
        all_examples, only_examples, all_except_harness=args.all_except_harness
    )
    if args.curated_only:
        curated = {
            "pydisplay_demo",
            "calculator",
            "paint",
            "eventsys_simpletest",
            "graphics_simpletest",
            "framebuf_simpletest",
            "color_test",
            "chango",
        }
        examples = {k: v for k, v in examples.items() if k in curated}
        display_only = {k: v for k, v in display_only.items() if k in curated}

    if args.order == "examples":
        rows = test_all_examples(
            examples,
            runtimes,
            manifest_defaults,
            runtime_defaults,
            fail_fast=args.fail_fast,
            verbose=args.verbose,
        )
    else:
        rows = test_all_runtimes(
            examples,
            runtimes,
            manifest_defaults,
            runtime_defaults,
            fail_fast=args.fail_fast,
            verbose=args.verbose,
        )

    rows = append_display_rows(rows, display_only, runtimes, all_examples)

    if args.json:
        print(json.dumps(rows, indent=2))

    print()
    print_table(rows, args.order)

    out_path = (
        Path(args.results_json)
        if args.results_json
        else REPO / ".cursor" / "example_test_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"\nFull results: {out_path}", file=sys.stderr)

    return compute_exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
