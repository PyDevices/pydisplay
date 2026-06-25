#!/usr/bin/env python3
"""
gen_demo_pages.py — generate the PyScript demo pages for pydisplay examples.

For every example whose header comment is ``# multimer types: async`` or
``# multimer types: all`` (the browser-runnable set), **and** whose
``# pyscript files:`` list contains only ``.py`` paths, this writes a styled,
self-contained page under ``html/`` and refreshes the card grids in
``index.html`` between the ``GEN:`` markers.

Run from anywhere:

    python tools/gen_demo_pages.py            # write pages + update index
    python tools/gen_demo_pages.py --check    # fail if anything is stale

Why pages are gated behind a "Run" button
------------------------------------------
Many examples (especially the ``all`` set) run a blocking ``while True`` loop at
import time. On PyScript's single main thread that would freeze the browser tab
on load. Each generated page therefore loads the runtime first and only
installs + imports the example when the user clicks **Run**, so nothing hangs
unexpectedly and the user opts in per example.

Each example declares install paths on line 2::

    # multimer types: async
    # pyscript files: calculator.py

Use comma-separated paths relative to ``src/examples/``. List non-``.py`` assets
too (``.bmp``, ``.bin``, …) for device installs; examples with any non-``.py``
entry are omitted from the browser gallery.

This script is CPython standard library only.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "src" / "examples"
HTML_DIR = REPO_ROOT / "html"
INDEX = REPO_ROOT / "index.html"
BOARD_CONFIG = REPO_ROOT / "src" / "lib" / "board_config.py"


def board_display_size() -> tuple[int, int]:
    """Read ``width`` / ``height`` from the PyScript ``board_config`` (layout hint only)."""
    width = height = None
    for line in BOARD_CONFIG.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("width = "):
            width = int(stripped.split("=", 1)[1].strip())
        elif stripped.startswith("height = "):
            height = int(stripped.split("=", 1)[1].strip())
    return width or 320, height or 480


# Example types we build pages for (anything async-compatible runs in PyScript).
TARGET_TYPES = ("async", "all")

# Curated copy. Anything omitted falls back to the module docstring + defaults.
# Fields: title, blurb, howto (list), experimental (bool), note (str), icon.
CURATED: dict[str, dict] = {
    "pydisplay_demo_async": {
        "title": "pydisplay Demo",
        "blurb": "The flagship showcase: auto-scrolling notes with on-screen buttons to rotate the display and cycle the accent color.",
        "howto": [
            "The notes panel scrolls automatically.",
            "Tap <strong>Rotate</strong> to turn the screen 90&deg;.",
            "Tap <strong>Color</strong> to cycle the accent.",
        ],
        "icon": "display",
    },
    "calculator": {
        "title": "Calculator",
        "blurb": "A touch calculator drawn with <code>graphics.FrameBuffer</code> and the material-design palette.",
        "howto": [
            "Click the number and operator keys.",
            "<code>C</code> clears, <code>=</code> evaluates.",
            "<code>Sqrt</code>, <code>%</code> and <code>+/-</code> act on the current entry.",
        ],
        "icon": "calc",
    },
    "paint": {
        "title": "Paint",
        "blurb": "A minimal paint program showing how <code>displaysys</code> handles pointer events.",
        "howto": [
            "Click a color block in the palette strip to select it.",
            "Left-drag on the canvas to paint.",
            "Right-click a swatch to flood-fill the canvas.",
        ],
        "icon": "paint",
        "extra_action": ('<a class="btn" href="./editor.html">Open in editor</a>'),
    },
    "eventsys_simpletest": {
        "title": "Event System",
        "blurb": "The smallest <code>eventsys</code> example &mdash; prints every pointer event it polls.",
        "howto": [
            "Hover and click over the black display area.",
            "Events are printed in the console panel to the right.",
            "This example has no on-screen drawing by design.",
        ],
        "icon": "event",
    },
    "apollo": {
        "title": "Apollo DSKY",
        "blurb": "An Apollo Guidance Computer DSKY emulator rendered from a BMP565 sprite sheet, with a live clock.",
        "howto": [
            "Tap the keypad buttons on the panel.",
            "The status lights and clock update live.",
            "The bottom key scrolls the readout.",
        ],
        "experimental": True,
        "note": "Depends on the apollo_dsky package and a binary BMP asset; designed for a 320&times;480 display.",
        "icon": "rocket",
    },
    "lv_test_timer_async": {
        "title": "LVGL Timer (async)",
        "blurb": "Drives an LVGL UI from a <code>multimer.aio</code> timer on the asyncio loop.",
        "howto": [
            "Builds a small LVGL UI and refreshes it from an async timer.",
            "Requires an <code>lvgl</code> binding in the runtime.",
            "Provided as a reference for async LVGL integration.",
        ],
        "experimental": True,
        "note": "LVGL is a native binding; this needs an <code>lvgl</code>-enabled runtime, which the bundled PyScript MicroPython does not include.",
        "icon": "timer",
    },
    "nano_gui_simpletest": {
        "experimental": True,
        "note": "Imports the <code>gui</code> (nano-gui) package, which is not bundled in <code>pyscript.toml</code>; expect an import error until it is added.",
    },
}

# Small inline SVG icon set, keyed by name.
ICONS = {
    "display": '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18M7 14h6"/>',
    "calc": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h4"/>',
    "paint": '<path d="M12 19l7-7a2.8 2.8 0 0 0-4-4l-7 7M11 9l4 4"/><path d="M7 14l-3 3 3 3 3-3"/>',
    "event": '<path d="M3 3l7 19 2-8 8-2z"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.5-2 5-2 5s3.5-.5 5-2c.9-.9.9-2.3 0-3.2a2.3 2.3 0 0 0-3 .2z"/><path d="M12 15l-3-3a11 11 0 0 1 9-7 11 11 0 0 1-7 9z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    "timer": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 3h6"/>',
    "type": '<path d="M4 7V5h16v2M9 19h6M12 5v14"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>',
    "shapes": '<circle cx="8" cy="8" r="4"/><path d="M14 13h7v7h-7z"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "scroll": '<path d="M8 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2h-2M9 12h6M9 16h6M9 8h6"/>',
}

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
BRAND_LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>'
SRC_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/></svg>'


def icon_svg(name: str) -> str:
    body = ICONS.get(name, ICONS["monitor"])
    return (
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


class Example:
    def __init__(self, name: str, import_name: str, source_rel: str, kind: str):
        self.name = name  # page/file stem, e.g. "calculator"
        self.import_name = import_name  # python import target, e.g. "chango"
        self.source_rel = source_rel  # path under repo, e.g. "src/examples/x.py"
        self.kind = kind  # "module" or "package"
        self.mtype = ""  # "async" | "all" | ...
        self.docstring_blurb = ""
        self.blocks = False  # blocking while-True without await
        self.is_async = False
        self.pyscript_files: list[str] = []  # paths relative to src/examples/

    # ---- derived metadata ----
    @property
    def curated(self) -> dict:
        return CURATED.get(self.name, {})

    @property
    def title(self) -> str:
        return self.curated.get("title") or self.name.replace("_", " ").title()

    @property
    def blurb(self) -> str:
        return (
            self.curated.get("blurb")
            or self.docstring_blurb
            or (f"The <code>{self.name}</code> example running in the browser via PyScript.")
        )

    @property
    def icon(self) -> str:
        if "icon" in self.curated:
            return self.curated["icon"]
        n = self.name
        if "font" in n or n in ("hello", "chango", "noto_fonts", "fonts"):
            return "type"
        if any(k in n for k in ("bmp", "pbm", "png", "logo", "displaybuf")):
            return "image"
        if "event" in n:
            return "event"
        if "scroll" in n:
            return "scroll"
        if any(k in n for k in ("graphics", "boxlines", "feathers", "color", "rotation")):
            return "shapes"
        return "monitor"

    @property
    def experimental(self) -> bool:
        return bool(self.curated.get("experimental"))

    @property
    def browser_eligible(self) -> bool:
        return all(path.endswith(".py") for path in self.pyscript_files)

    @property
    def install_line(self) -> str:
        return render_mip_installs(self.pyscript_files)

    @property
    def primary_tag(self) -> tuple[str, str]:
        if self.experimental:
            return ("warn", "experimental")
        return ("async", "async") if self.mtype == "async" else ("all", "all")

    @property
    def source_url(self) -> str:
        return f"https://github.com/PyDevices/pydisplay/blob/main/{self.source_rel}"


def parse_pyscript_files(lines: list[str]) -> list[str]:
    for line in lines[:5]:
        s = line.strip()
        if s.startswith("# pyscript files:"):
            body = s.split(":", 1)[1].strip()
            return [part.strip() for part in body.split(",") if part.strip()]
    return []


def mip_install_target(examples_rel: str) -> str | None:
    if "/" in examples_rel:
        return f"examples/{examples_rel.split('/', maxsplit=1)[0]}"
    return None


def render_mip_installs(pyscript_files: list[str]) -> str:
    ind = "                "
    br = "                    "
    lines = [
        "from js import document",
        f"{ind}_host = document.location.hostname",
        f'{ind}_local = _host in ("127.0.0.1", "localhost")',
    ]
    for path in pyscript_files:
        target = mip_install_target(path)
        if target:
            local = (
                f"mip.install(document.location.origin + "
                f'"/src/examples/{path}", target="{target}")'
            )
            gh = (
                f'mip.install("github:PyDevices/pydisplay/src/examples/{path}", target="{target}")'
            )
        else:
            local = f'mip.install(document.location.origin + "/src/examples/{path}")'
            gh = f'mip.install("github:PyDevices/pydisplay/src/examples/{path}")'
        lines.append(f"{ind}if _local:")
        lines.append(f"{br}{local}")
        lines.append(f"{ind}else:")
        lines.append(f"{br}{gh}")
    return "\n".join(lines)


def parse_example(path: Path) -> Example | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    mtype = ""
    for line in lines[:5]:
        s = line.strip()
        if s.startswith("# multimer types:"):
            mtype = s.split(":", 1)[1].strip().lower()
            break
    if not mtype:
        return None
    # Normalise: treat the set membership loosely.
    type_tokens = {t.strip() for t in mtype.replace(";", ",").split(",")}
    chosen = next((t for t in TARGET_TYPES if t in type_tokens), None)
    if chosen is None:
        return None

    rel = path.relative_to(REPO_ROOT).as_posix()
    if path.parent.name == "examples":
        name = path.stem
        import_name = path.stem
        kind = "module"
    else:
        # Sub-package example, e.g. chango/chango.py -> import "chango".
        name = path.parent.name
        import_name = path.parent.name
        kind = "package"

    ex = Example(name, import_name, rel, kind)
    ex.mtype = chosen
    ex.is_async = (chosen == "async") or ("multimer.aio" in text) or ("async def main" in text)
    ex.blocks = ("while True" in text) and not ex.is_async
    ex.docstring_blurb = extract_blurb(text, name)
    examples_rel = path.relative_to(EXAMPLES_DIR).as_posix()
    ex.pyscript_files = parse_pyscript_files(lines) or [examples_rel]
    for entry in ex.pyscript_files:
        if not (EXAMPLES_DIR / entry).is_file():
            raise SystemExit(f"{rel}: missing pyscript file {entry}")
    return ex


def extract_blurb(text: str, name: str) -> str:
    """Pull a short human sentence out of the module docstring."""
    start = None
    for q in ('"""', "'''"):
        i = text.find(q)
        if i != -1 and (start is None or i < start[0]):
            start = (i, q)
    if not start:
        return ""
    i, q = start
    end = text.find(q, i + 3)
    if end == -1:
        return ""
    doc = text[i + 3 : end]
    skip = {name, f"{name}.py", "=" * len(name)}
    for raw in doc.splitlines():
        line = raw.strip()
        if not line or line in skip or set(line) <= {"=", "-", "~"}:
            continue
        if line.startswith((".. ", ":", "-", "*", "https://", "http://")):
            continue
        # Trim to one sentence-ish, escape angle brackets.
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return line[:160]
    return ""


def discover() -> list[Example]:
    found: dict[str, Example] = {}
    for path in sorted(EXAMPLES_DIR.rglob("*.py")):
        # Only top-level files and one-level sub-package entry files.
        rel = path.relative_to(EXAMPLES_DIR)
        if len(rel.parts) == 1 or (len(rel.parts) == 2 and rel.parts[0] == rel.stem):
            ex = parse_example(path)
        else:
            ex = None
        if ex and ex.browser_eligible and ex.name not in found:
            found[ex.name] = ex
    return list(found.values())


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def render_howto(ex: Example) -> str:
    items = ex.curated.get("howto")
    if not items:
        if ex.blocks:
            items = [
                "Click <strong>Run</strong> to install and start the example.",
                "This example runs a continuous loop &mdash; see the note.",
                "Interact over the display where supported.",
            ]
        else:
            items = [
                "Click <strong>Run</strong> to install and start the example.",
                "Output (if any) appears in the console panel to the right.",
            ]
    return "\n".join(f"                        <li>{i}</li>" for i in items)


def render_note(ex: Example) -> str:
    notes = []
    if ex.curated.get("note"):
        notes.append(ex.curated["note"])
    if ex.blocks:
        notes.append(
            "Runs a blocking animation loop, so the browser tab may become "
            "unresponsive after <strong>Run</strong>. Reload the page to stop it."
        )
    if not notes:
        return ""
    body = " ".join(notes)
    return f"""                <div class="panel">
                    <h2>Note</h2>
                    <ul><li>{body}</li></ul>
                </div>
"""


def render_tags(ex: Example) -> str:
    tags = []
    cls, label = ("async", "async") if ex.mtype == "async" else ("all", "all")
    tags.append(f'<span class="tag {cls}">{label}</span>')
    if ex.experimental:
        tags.append('<span class="tag warn">experimental</span>')
    if ex.blocks:
        tags.append('<span class="tag loops">loops</span>')
    return "\n            ".join(tags)


def render_install_meta(ex: Example) -> str:
    n = len(ex.pyscript_files)
    return "1 file" if n == 1 else f"{n} files"


def render_page(ex: Example) -> str:
    extra_action = (
        ex.curated.get("extra_action") or '<a class="btn" href="../index.html">Back to demos</a>'
    )
    note_html = render_note(ex)
    display_w, display_h = board_display_size()
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{ex.title} — pydisplay demo</title>
    <meta name="description" content="{ex.title}: a pydisplay example running in the browser via PyScript.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
    <link rel="stylesheet" href="./demo.css">
    <link rel="stylesheet" href="./pyscript/core.css">
    <script src="./mini-coi-fd.js"></script>
    <script type="module" src="./pyscript/core.js"></script>
</head>
<body>
    <header class="site-header">
        <div class="wrap">
            <a class="brand" href="../index.html">
                <span class="logo">{BRAND_LOGO}</span>
                py<span class="accent">display</span>
            </a>
            <nav class="nav">
                <a href="../index.html">Demos</a>
                <a href="https://pydisplay.readthedocs.io">Docs</a>
                <a href="https://github.com/PyDevices/pydisplay">GitHub</a>
            </nav>
        </div>
    </header>

    <main class="wrap example-main">
        <nav class="crumbs">
            <a href="../index.html">Demos</a>
            <span class="sep">/</span>
            <span>{ex.title}</span>
        </nav>

        <div class="example-head">
            <h1>{ex.title}</h1>
            {render_tags(ex)}
        </div>
        <p class="example-lede">{ex.blurb}</p>

        <div class="play-area">
            <div class="loading" id="loading">
                <span class="spinner"></span> <span id="status">Loading PyScript runtime…</span>
            </div>
            <div class="display-column">
                <div class="device">
                    <canvas id="display_canvas" width="{display_w}" height="{display_h}"></canvas>
                </div>
                <div class="run-bar">
                    <button id="run-btn" class="btn primary" disabled>Run</button>
                </div>
            </div>

            <section class="console-panel" aria-label="Console output">
                <h2 class="console-label">Console output</h2>
                <div id="log" class="log"></div>
            </section>
        </div>

        <div class="meta-layout">
            <aside class="aside">
                <div class="panel">
                    <h2>How to use</h2>
                    <ul>
{render_howto(ex)}
                    </ul>
                </div>
{note_html}                <div class="panel">
                    <h2>Details</h2>
                    <div class="meta-row"><span class="k">Source</span><span class="v">{Path(ex.source_rel).name}</span></div>
                    <div class="meta-row"><span class="k">Type</span><span class="v">{ex.mtype}</span></div>
                    <div class="meta-row"><span class="k">Install</span><span class="v">{render_install_meta(ex)}</span></div>
                </div>
                <div class="actions">
                    <a class="btn" href="{ex.source_url}" target="_blank" rel="noopener">{SRC_ICON} View source</a>
                    {extra_action}
                </div>
            </aside>
        </div>

    </main>

    <footer class="site-footer">
        <div class="wrap">
            <span>pydisplay — cross-platform display &amp; event drivers</span>
            <span><a href="https://github.com/PyDevices/pydisplay">PyDevices/pydisplay</a></span>
        </div>
    </footer>

    <!-- Loader is gated behind the Run button so blocking examples never hang on load. -->
    <script type="mpy" config="./pyscript.toml" output="log">
        import builtins
        from js import document
        from pyscript.ffi import create_proxy

        def _log_print(*args, **kwargs):
            el = document.getElementById("log")
            if el is not None:
                sep = kwargs.get("sep", " ")
                end = kwargs.get("end", "\\n")
                el.textContent += sep.join(str(a) for a in args) + end
                el.scrollTop = el.scrollHeight

        builtins.print = _log_print

        _status = document.getElementById("status")
        _btn = document.getElementById("run-btn")
        _started = False

        def _set(msg):
            if _status:
                _status.textContent = msg

        def _start(*_):
            global _started
            if _started:
                return
            _started = True
            _btn.disabled = True
            _btn.textContent = "Running…"
            try:
                _set("Installing modules…")
                import mip
                {ex.install_line}
                _set("Importing {ex.import_name}…")
                import lib.path
                import {ex.import_name}
                _set("Running.")
            except Exception as e:
                _log_print("Run failed:", e)
                _set("Error — see console.")
                raise

        _btn.addEventListener("click", create_proxy(_start))
        _btn.disabled = False
        _set("Runtime ready — click Run.")
        print("PyScript runtime ready. Click Run to start {ex.name}.")
    </script>

    <script>
        // Stop the spinner once the runtime is ready (Run button enabled).
        const _btn = document.getElementById('run-btn');
        const _spin = document.querySelector('#loading .spinner');
        const _t = setInterval(() => {{
            if (_btn && !_btn.disabled) {{
                if (_spin) _spin.style.display = 'none';
                clearInterval(_t);
            }}
        }}, 150);
    </script>

    <script>
        // Match console chrome height to the display bezel; log fills the remainder.
        (function () {{
            const device = document.querySelector('.play-area .device');
            const panel = document.querySelector('.play-area .console-panel');
            const log = document.getElementById('log');
            if (!device || !panel || !log) return;
            function syncConsoleHeight() {{
                if (window.innerWidth <= 880) {{
                    panel.style.height = '';
                    return;
                }}
                const h = device.getBoundingClientRect().height;
                if (h > 0) {{
                    panel.style.height = h + 'px';
                }}
            }}
            syncConsoleHeight();
            window.addEventListener('resize', syncConsoleHeight);
            if (typeof ResizeObserver !== 'undefined') {{
                new ResizeObserver(syncConsoleHeight).observe(device);
            }}
        }})();
    </script>
</body>
</html>
'''


def render_card(ex: Example, base: str = "html/") -> str:
    cls, label = ex.primary_tag
    return f'''                <a class="card" href="{base}{ex.name}.html">
                    <div class="card-top">
                        <span class="card-icon">{icon_svg(ex.icon)}</span>
                        <span class="tag {cls}">{label}</span>
                    </div>
                    <h3>{ex.title}</h3>
                    <p>{ex.blurb}</p>
                    <span class="go">Open demo {ARROW}</span>
                </a>'''


def render_cards(examples: list[Example]) -> str:
    return "\n".join(render_card(ex) for ex in examples)


def replace_block(text: str, key: str, payload: str) -> str:
    start = f"<!-- GEN:{key}:start -->"
    end = f"<!-- GEN:{key}:end -->"
    si = text.find(start)
    ei = text.find(end)
    if si == -1 or ei == -1:
        raise SystemExit(f"index.html is missing the {start}/{end} markers")
    return text[: si + len(start)] + "\n" + payload + "\n            " + text[ei:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="fail if any output is stale")
    args = parser.parse_args(argv)

    examples = discover()
    by_type = {"async": [], "all": []}
    for ex in sorted(examples, key=lambda e: (e.experimental, e.title.lower())):
        by_type[ex.mtype].append(ex)

    stale: list[str] = []

    def write(path: Path, content: str) -> None:
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == content:
            return
        if args.check:
            stale.append(str(path.relative_to(REPO_ROOT)))
            return
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")

    for ex in examples:
        write(HTML_DIR / f"{ex.name}.html", render_page(ex))

    index_text = INDEX.read_text(encoding="utf-8")
    index_text = replace_block(index_text, "async", render_cards(by_type["async"]))
    index_text = replace_block(index_text, "all", render_cards(by_type["all"]))
    write(INDEX, index_text)

    print(
        f"\n{len(examples)} example pages "
        f"({len(by_type['async'])} async, {len(by_type['all'])} all)."
    )
    if args.check and stale:
        print("STALE:\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
