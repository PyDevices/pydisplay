#!/usr/bin/env python3
"""
serve.py — local development server for the pydisplay PyScript site.

Point it at the repo root (the default) and it serves the static PyScript
site the same way GitHub Pages does, but from the source tree so you can edit
and refresh:

    python tools/serve.py
    # then open:
    #   http://127.0.0.1:8000/web/pyscript/index.html       (gallery)
    #   http://127.0.0.1:8000/web/pyscript/micropython.html?modules=calc_graphics,calc_engine
    #   http://127.0.0.1:8000/web/landing/index.html      (marketing landing)

Why a custom server instead of `python -m http.server`?

1. Cross-origin isolation headers (COOP/COEP/CORP).
   PyScript's worker-backed pages (REPL, simple) need
   SharedArrayBuffer, which the browser only enables on a cross-origin-isolated
   page. In production the bundled `mini-coi-fd.js` service worker injects these
   headers; this server sends the *same* headers directly so local behaviour
   matches production (and so the service worker doesn't have to reload the
   page on first visit). Use --no-coi to turn this off.

2. A debug log sink for Cursor Debug mode.
   Cursor's Debug mode (and ad-hoc browser instrumentation) can capture
   console logs, errors and network activity in the page. This server exposes a
   permissive endpoint at /__debug that accepts POST (and OPTIONS preflight)
   from the page and prints whatever it receives to this terminal, so a desktop
   debugging session can stream browser-side events back to the shell. The
   endpoint is intentionally simple and CORS-open; see `post_debug_log()` in the
   page-side snippet printed at startup, or wire your own beacon to it.

Everything here is CPython standard library only — no third-party deps.
"""

from __future__ import annotations

import argparse
import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent.parent

# Path prefix the page-side debug beacon POSTs to. Anything under it is treated
# as a log sink so Cursor Debug mode tooling can pick its own sub-paths.
DEBUG_PREFIX = "/__debug"

# Same-origin path for micropip LVGL wheels (pyodide.html). When the tree does
# not yet contain wheels/, link a sibling lv_cpython_mod build if present.
# Last resort: mirror the published Pages index + wheel (needs CORP via this
# server — cross-origin Pages lacks Cross-Origin-Resource-Policy under COEP).
WHEELS_DIR = REPO_ROOT / "web" / "pyscript" / "wheels"
SIBLING_WHEEL_DIRS = (
    REPO_ROOT.parent / "lv_cpython_mod" / "web" / "wheels",
    REPO_ROOT.parent / "cmods" / "lv_cpython_mod" / "web" / "wheels",
)
PAGES_WHEELS_BASE = "https://pydevices.github.io/lv_cpython_mod/wheels/"


def _mirror_pages_wheels() -> Path | None:
    """Download lvgl.json + wheel from lv_cpython_mod Pages into web/pyscript/wheels/."""
    try:
        WHEELS_DIR.mkdir(parents=True, exist_ok=True)
        index_url = PAGES_WHEELS_BASE + "lvgl.json"
        with urllib.request.urlopen(index_url, timeout=60) as resp:
            raw = resp.read()
        data = json.loads(raw)
        wheel_name = data.get("wheel")
        if not isinstance(wheel_name, str) or not wheel_name.endswith(".whl"):
            raise ValueError(f"invalid wheel entry in {index_url}: {wheel_name!r}")
        if "/" in wheel_name or wheel_name.startswith("."):
            raise ValueError(f"unsafe wheel filename: {wheel_name!r}")
        (WHEELS_DIR / "lvgl.json").write_bytes(raw)
        wheel_path = WHEELS_DIR / wheel_name
        if not wheel_path.is_file():
            print(f"  wheels: downloading {wheel_name} from Pages…")
            urllib.request.urlretrieve(PAGES_WHEELS_BASE + wheel_name, wheel_path)
        print(f"  wheels:                  {WHEELS_DIR} (mirrored from Pages)")
        return WHEELS_DIR
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"warning: could not mirror LVGL wheels from Pages: {exc}", file=sys.stderr)
        return None


def ensure_wheels_dir() -> Path | None:
    """Prefer an in-tree wheels/ dir; otherwise symlink a sibling lv_cpython_mod build."""
    if WHEELS_DIR.is_dir() and any(WHEELS_DIR.glob("*.whl")):
        return WHEELS_DIR
    if WHEELS_DIR.is_symlink():
        try:
            WHEELS_DIR.unlink()
        except OSError:
            return None
    elif WHEELS_DIR.is_dir():
        # Empty or non-wheel dir — leave alone so we never clobber content.
        if any(WHEELS_DIR.iterdir()):
            return WHEELS_DIR if any(WHEELS_DIR.glob("*.whl")) else None
        try:
            WHEELS_DIR.rmdir()
        except OSError:
            return None
    for src in SIBLING_WHEEL_DIRS:
        if src.is_dir() and any(src.glob("*.whl")):
            try:
                WHEELS_DIR.symlink_to(src.resolve(), target_is_directory=True)
            except OSError as exc:
                print(f"warning: could not link {WHEELS_DIR} → {src}: {exc}", file=sys.stderr)
                return None
            print(f"  wheels:                  {WHEELS_DIR} → {src}")
            return WHEELS_DIR
    return _mirror_pages_wheels()


def _stamp() -> str:
    now = datetime.datetime.now(datetime.UTC)
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


class DemoRequestHandler(SimpleHTTPRequestHandler):
    """Static handler that adds COI headers and a debug log sink."""

    # Set per-process from CLI args (see main()).
    coi_enabled = True

    # Keep pages fresh while editing.
    def end_headers(self) -> None:  # noqa: D401 - http.server hook
        self.send_header("Cache-Control", "no-store, must-revalidate")
        if self.coi_enabled:
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        super().end_headers()

    def _is_debug(self) -> bool:
        return self.path == DEBUG_PREFIX or self.path.startswith(DEBUG_PREFIX + "/")

    def _send_cors(self, status: int = 204) -> None:
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802 - http.server hook
        if self._is_debug():
            self._send_cors()
            return
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - http.server hook
        if not self._is_debug():
            self.send_error(404, "Not Found")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self._log_debug(raw)
        self._send_cors()

    def do_GET(self) -> None:  # noqa: N802 - http.server hook
        if self._is_debug():
            self._send_cors(200)
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - http.server hook
        if self._is_debug():
            self._send_cors(200)
            return
        super().do_HEAD()

    def _log_debug(self, raw: bytes) -> None:
        stamp = _stamp()
        text = raw.decode("utf-8", "replace").strip()
        payload = None
        try:
            payload = json.loads(text)
            text = json.dumps(payload, ensure_ascii=False, indent=2)
        except (ValueError, TypeError):
            pass
        client = self.address_string()
        if isinstance(payload, dict) and payload.get("level") == "timing":
            label = (payload.get("args") or ["?"])[0]
            sys.stdout.write(f"\n[timing {stamp}] {label}\n")
        else:
            sys.stdout.write(f"\n[debug {stamp} {client}] {self.path}\n{text}\n")
        sys.stdout.flush()

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002 - http.server hook
        stamp = _stamp()
        sys.stderr.write(f"[{stamp}] {self.address_string()} {fmt % args}\n")


PAGE_SNIPPET = """\
// Page-side beacon for Cursor Debug mode (paste into a demo page or console):
//   fetch('/__debug', {method: 'POST', body: JSON.stringify({
//     level: 'log', msg: 'hello from the page', url: location.href})});
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(REPO_ROOT),
        help="directory to serve (default: repo root)",
    )
    parser.add_argument("-p", "--port", type=int, default=8000, help="port (default: 8000)")
    parser.add_argument(
        "-b", "--bind", default="127.0.0.1", help="bind address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--no-coi", action="store_true", help="do not send cross-origin isolation headers"
    )
    args = parser.parse_args(argv)

    root = Path(args.directory).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    DemoRequestHandler.coi_enabled = not args.no_coi
    handler = partial(DemoRequestHandler, directory=str(root))

    httpd = ThreadingHTTPServer((args.bind, args.port), handler)
    base = f"http://{args.bind}:{args.port}"

    print(f"pydisplay PyScript server — serving {root}")
    print(f"  cross-origin isolation: {'on' if DemoRequestHandler.coi_enabled else 'off'}")
    print(f"  debug log sink:         POST {base}{DEBUG_PREFIX}")
    if root == REPO_ROOT:
        ensure_wheels_dir()
    print("")
    print("Open one of:")
    print(f"  {base}/web/pyscript/index.html")
    print(f"  {base}/web/pyscript/micropython.html?modules=calc_graphics,calc_engine")
    print(f"  {base}/web/pyscript/pyodide.html?modules=calc_lvgl,calc_engine")
    print(f"  {base}/web/pyscript/embed.html?modules=calc_graphics,calc_engine")
    print(f"  {base}/web/landing/index.html")
    print("")
    print(PAGE_SNIPPET)
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
