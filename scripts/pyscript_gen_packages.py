#!/usr/bin/env python3
"""
pyscript_gen_packages.py — refresh the pydisplay PyScript browser gallery.

Scans ``src/examples/`` for ``# multimer types: async|all`` headers, then
resolves PyScript file lists automatically (with optional header overrides):

  - **Single-file examples** — the entry ``.py`` only
  - **Package examples** (``examples/<pkg>/<pkg>.py``) — all ``.py`` files under
    ``examples/<pkg>/``, minus any ``# pyscript skip:`` paths
  - **Multi-module examples** — entry plus same-directory imports discovered from
    ``import`` / ``from … import`` (e.g. ``lv_test_timer_async`` + ``common``)

Optional headers (first 10 lines):

  - ``# pyscript files:`` — explicit override (legacy; still used when listing
    both Python and binary paths in one comment)
  - ``# pyscript binaries:`` — non-``.py`` assets; example is excluded from the
    browser gallery when any path has a binary suffix
  - ``# pyscript skip:`` — ``examples/``-relative ``.py`` paths or directories
    omitted from package auto-discovery (e.g. ``my_pkg/dev`` skips all ``.py``
    files under that tree); the token ``gallery`` excludes the example from the
    browser card grid (multimer tag unchanged)
  - ``# pyscript modules:`` — extra ``examples/``-relative ``.py`` paths for
    multi-module loaders when import scanning is insufficient

Then:

  - Updates gallery cards in ``web/pyscript/index.html`` (between ``GEN:`` markers)
  - Writes ``web/pyscript/<name>.json`` MIP manifests for multi-file examples
  - Deletes stale ``web/pyscript/*.html`` from the old per-demo page generator

Every gallery example opens the parametric loader at ``load.html?modules=…`` or
``load.html?manifests=…``.

    python scripts/pyscript_gen_packages.py
    python scripts/pyscript_gen_packages.py --check
    python scripts/pyscript_gen_packages.py --copy-examples DIR   # GitHub Pages deploy
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import re
import shutil
import sys

_scripts = Path(__file__).resolve().parent
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
from personal_examples import PERSONAL_EXAMPLE_DIRS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "src" / "examples"
PYSCRIPT_DIR = REPO_ROOT / "web" / "pyscript"
INDEX = PYSCRIPT_DIR / "index.html"

MIP_REPO = "github:PyDevices/pydisplay/"
MIP_MANIFEST_VERSION = "0.0.5"

TARGET_TYPES = ("async", "all")
BINARY_SUFFIXES = frozenset({".bmp", ".bin", ".pbm", ".png", ".jpg", ".jpeg", ".gif", ".webp"})
KEEP_HTML = frozenset({"index", "load", "repl", "editor", "test", "embed"})
LOADER_BASE = "load.html"

ARROW = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)

# Curated card copy. Omitted fields fall back to defaults / docstring.
CURATED: dict[str, dict] = {
    "pydisplay_demo_async": {
        "title": "pydisplay Demo",
        "blurb": "The flagship showcase: auto-scrolling notes with on-screen buttons to rotate the display and cycle the accent color.",
        "icon": "display",
    },
    "calculator": {
        "title": "Calculator",
        "blurb": "A touch calculator drawn with <code>graphics.FrameBuffer</code> and the material-design palette.",
        "icon": "calc",
    },
    "paint": {
        "title": "Paint",
        "blurb": "A minimal paint program showing how <code>displaysys</code> handles pointer events.",
        "icon": "paint",
    },
    "eventsys_simpletest": {
        "title": "Event System",
        "blurb": "The smallest <code>eventsys</code> example &mdash; prints every pointer event it polls.",
        "icon": "event",
    },
    "apollo": {
        "title": "Apollo DSKY",
        "blurb": "An Apollo Guidance Computer DSKY emulator rendered from a BMP565 sprite sheet, with a live clock.",
        "experimental": True,
        "icon": "rocket",
    },
    "lv_test_timer_async": {
        "title": "LVGL Timer (async)",
        "blurb": "Drives an LVGL UI from a <code>multimer</code> timer on the asyncio loop.",
        "experimental": True,
        "icon": "timer",
    },
    "nano_gui_simpletest": {
        "experimental": True,
    },
}

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


def icon_svg(name: str) -> str:
    body = ICONS.get(name, ICONS["monitor"])
    return (
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


class Example:
    """One browser-gallery demo discovered from ``src/examples/``."""

    def __init__(self, name: str, source_rel: str, kind: str):
        self.name = name
        self.source_rel = source_rel
        self.kind = kind  # "module" | "manifest"
        self.mtype = ""
        self.docstring_blurb = ""
        self.pyscript_files: list[str] = []
        self.pyscript_binaries: list[str] = []

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
            or f"The <code>{self.name}</code> demo running in the browser via PyScript."
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
    def depends_on_binary_files(self) -> bool:
        paths = self.pyscript_files + self.pyscript_binaries
        return any(Path(path).suffix.lower() in BINARY_SUFFIXES for path in paths)

    @property
    def browser_eligible(self) -> bool:
        return not self.depends_on_binary_files

    def loader_href(self, base: str = LOADER_BASE) -> str:
        if self.kind == "module":
            stems = ",".join(Path(path).stem for path in self.pyscript_files)
            return f"{base}?modules={stems}"
        return f"{base}?manifests={self.name}"

    @property
    def primary_tag(self) -> tuple[str, str]:
        if self.experimental:
            return ("warn", "experimental")
        return ("async", "async") if self.mtype == "async" else ("all", "all")


HEADER_SCAN_LINES = 10

LOCAL_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.MULTILINE,
)


def parse_header_list(lines: list[str], prefix: str) -> list[str]:
    for line in lines[:HEADER_SCAN_LINES]:
        s = line.strip()
        if s.startswith(prefix):
            body = s.split(":", 1)[1].strip()
            return [part.strip() for part in body.split(",") if part.strip()]
    return []


def _py_sort_key(rel: str) -> tuple:
    parts = rel.split("/")
    name = parts[-1]
    init_first = 0 if name == "__init__.py" else 1
    return (parts[:-1], init_first, name)


def _is_skipped(rel: str, skip: set[str]) -> bool:
    if rel in skip:
        return True
    for entry in skip:
        prefix = entry.rstrip("/")
        if rel.startswith(prefix + "/"):
            return True
    return False


def discover_package_py_files(name: str, skip: set[str]) -> list[str]:
    pkg_dir = EXAMPLES_DIR / name
    if not pkg_dir.is_dir():
        raise SystemExit(f"examples/{name}: package directory missing")
    paths: list[str] = []
    for path in sorted(pkg_dir.rglob("*.py")):
        rel = path.relative_to(EXAMPLES_DIR).as_posix()
        if not _is_skipped(rel, skip):
            paths.append(rel)
    return sorted(paths, key=_py_sort_key)


def discover_local_py_imports(entry_path: Path, text: str) -> list[str]:
    """Same-directory modules and ``examples/<pkg>/`` packages imported by entry."""
    found: list[str] = []
    seen: set[str] = set()
    parent = entry_path.parent

    def add(rel: str) -> None:
        if rel not in seen:
            seen.add(rel)
            found.append(rel)

    for match in LOCAL_IMPORT_RE.finditer(text):
        mod = match.group(1) or match.group(2)
        if not mod or mod.startswith("."):
            continue
        top = mod.split(".")[0]
        same_dir = parent / f"{top}.py"
        if same_dir.is_file():
            add(same_dir.relative_to(EXAMPLES_DIR).as_posix())
            continue
        pkg_init = EXAMPLES_DIR / top / "__init__.py"
        if pkg_init.is_file():
            add(pkg_init.relative_to(EXAMPLES_DIR).as_posix())
    return found


def normalize_py_path(raw: str) -> str:
    return raw if raw.endswith(".py") else f"{raw}.py"


def finalize_py_files(py_files: list[str], entry_rel: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    if entry_rel in py_files:
        ordered.append(entry_rel)
        seen.add(entry_rel)
    for rel in sorted(py_files, key=_py_sort_key):
        if rel not in seen:
            ordered.append(rel)
            seen.add(rel)
    return ordered


def resolve_pyscript_paths(
    path: Path, kind: str, name: str, lines: list[str], text: str
) -> tuple[list[str], list[str]]:
    explicit = parse_header_list(lines, "# pyscript files:")
    extra_binaries = parse_header_list(lines, "# pyscript binaries:")
    if explicit:
        py_files = [
            entry for entry in explicit if Path(entry).suffix.lower() not in BINARY_SUFFIXES
        ]
        binaries = [entry for entry in explicit if Path(entry).suffix.lower() in BINARY_SUFFIXES]
        binaries.extend(extra_binaries)
        return py_files, binaries

    skip = set(parse_header_list(lines, "# pyscript skip:"))
    extra_modules = parse_header_list(lines, "# pyscript modules:")
    entry_rel = path.relative_to(EXAMPLES_DIR).as_posix()

    if kind == "manifest":
        py_files = discover_package_py_files(name, skip)
    else:
        py_files = [entry_rel]
        py_files.extend(discover_local_py_imports(path, text))
        for raw in extra_modules:
            rel = normalize_py_path(raw)
            if rel not in py_files:
                py_files.append(rel)
        py_files = finalize_py_files(py_files, entry_rel)

    return py_files, extra_binaries


def extract_blurb(text: str, name: str) -> str:
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
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return line[:160]
    return ""


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
    type_tokens = {t.strip() for t in mtype.replace(";", ",").split(",")}
    chosen = next((t for t in TARGET_TYPES if t in type_tokens), None)
    if chosen is None:
        return None
    if "gallery" in parse_header_list(lines, "# pyscript skip:"):
        return None

    rel = path.relative_to(REPO_ROOT).as_posix()
    rel_in_examples = path.relative_to(EXAMPLES_DIR)
    if path.parent.name == "examples":
        name = path.stem
        kind = "module"
    elif len(rel_in_examples.parts) == 2 and (
        rel_in_examples.parts[0] == rel_in_examples.stem
        or rel_in_examples.parts[0] == path.parent.name
    ):
        name = path.parent.name
        kind = "manifest"
    else:
        return None

    ex = Example(name, rel, kind)
    ex.mtype = chosen
    ex.docstring_blurb = extract_blurb(text, name)
    ex.pyscript_files, ex.pyscript_binaries = resolve_pyscript_paths(path, kind, name, lines, text)
    for entry in ex.pyscript_files:
        if not (EXAMPLES_DIR / entry).is_file():
            raise SystemExit(f"{rel}: missing pyscript file {entry}")
    for entry in ex.pyscript_binaries:
        if not (EXAMPLES_DIR / entry).is_file():
            raise SystemExit(f"{rel}: missing pyscript binary {entry}")
    return ex


def _is_personal_example(path: Path) -> bool:
    try:
        rel = path.relative_to(EXAMPLES_DIR)
    except ValueError:
        return False
    return bool(rel.parts) and rel.parts[0] in PERSONAL_EXAMPLE_DIRS


def example_py_files() -> list[Path]:
    """All ``*.py`` under ``src/examples/``, excluding personal symlink trees."""
    paths: list[Path] = []
    seen: set[str] = set()
    for path in sorted(EXAMPLES_DIR.rglob("*.py")):
        if _is_personal_example(path):
            continue
        paths.append(path)
        seen.add(str(path))
    for child in sorted(EXAMPLES_DIR.iterdir()):
        if child.name in PERSONAL_EXAMPLE_DIRS:
            continue
        if child.is_symlink():
            for path in sorted(child.rglob("*.py")):
                if _is_personal_example(path):
                    continue
                key = str(path)
                if key not in seen:
                    paths.append(path)
                    seen.add(key)
    return paths


def discover_parsed() -> list[Example]:
    found: dict[str, Example] = {}
    for path in example_py_files():
        ex = parse_example(path)
        if ex and ex.name not in found:
            found[ex.name] = ex
    return list(found.values())


def discover() -> list[Example]:
    return [ex for ex in discover_parsed() if ex.browser_eligible]


def example_mip_manifest(ex: Example) -> dict:
    # Paths relative to web/pyscript/ where the manifest is served.
    return {
        "urls": [[path, f"../../src/examples/{path}"] for path in ex.pyscript_files],
        "version": MIP_MANIFEST_VERSION,
    }


def render_card(ex: Example, base: str = LOADER_BASE) -> str:
    cls, label = ex.primary_tag
    return f'''                <a class="card" href="{ex.loader_href(base)}">
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
        raise SystemExit(f"{INDEX.name} is missing the {start}/{end} markers")
    return text[: si + len(start)] + "\n" + payload + "\n            " + text[ei:]


def write_html_mip_manifests(
    examples: list[Example], write: Callable[[Path, str], None], stale: list[str], check: bool
) -> None:
    keep = {ex.name for ex in examples if ex.kind == "manifest"}
    for ex in examples:
        if ex.kind != "manifest":
            continue
        write(
            PYSCRIPT_DIR / f"{ex.name}.json", json.dumps(example_mip_manifest(ex), indent=2) + "\n"
        )
    for path in PYSCRIPT_DIR.glob("*.json"):
        if path.stem in keep:
            continue
        rel = str(path.relative_to(REPO_ROOT))
        if check:
            stale.append(rel)
            continue
        path.unlink()
        print(f"removed {rel}")


def remove_stale_demo_html(stale: list[str], check: bool) -> None:
    """Remove leftover ``web/pyscript/<demo>.html`` files from the old per-demo generator."""
    for path in PYSCRIPT_DIR.glob("*.html"):
        if path.stem in KEEP_HTML:
            continue
        rel = str(path.relative_to(REPO_ROOT))
        if check:
            stale.append(rel)
            continue
        path.unlink()
        print(f"removed {rel}")


def gallery_example_files() -> list[str]:
    files: set[str] = set()
    for ex in discover():
        files.update(ex.pyscript_files)
    return sorted(files)


def copy_gallery_examples(dest: Path) -> int:
    n = 0
    for rel in gallery_example_files():
        src = EXAMPLES_DIR / rel
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="fail if any output is stale")
    parser.add_argument(
        "--copy-examples",
        type=Path,
        metavar="DIR",
        help="copy gallery example .py files into DIR (for GitHub Pages deploy)",
    )
    args = parser.parse_args(argv)

    if args.copy_examples:
        n = copy_gallery_examples(args.copy_examples)
        print(f"copied {n} gallery example file(s) to {args.copy_examples}")

    parsed = discover_parsed()
    skipped_binary = sorted(ex.name for ex in parsed if ex.depends_on_binary_files)
    examples = [ex for ex in parsed if ex.browser_eligible]
    by_type: dict[str, list[Example]] = {"async": [], "all": []}
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

    write_html_mip_manifests(examples, write, stale, args.check)
    remove_stale_demo_html(stale, args.check)

    index_text = INDEX.read_text(encoding="utf-8")
    index_text = replace_block(index_text, "async", render_cards(by_type["async"]))
    index_text = replace_block(index_text, "all", render_cards(by_type["all"]))
    write(INDEX, index_text)

    n_module = sum(1 for ex in examples if ex.kind == "module")
    n_manifest = sum(1 for ex in examples if ex.kind == "manifest")
    print(
        f"\n{len(examples)} gallery demo(s) "
        f"({n_module} module, {n_manifest} manifest; "
        f"{len(by_type['async'])} async, {len(by_type['all'])} all)."
    )
    if skipped_binary:
        print(
            f"Skipped {len(skipped_binary)} binary-dependent demo(s): " + ", ".join(skipped_binary)
        )
    if args.check and stale:
        print("STALE:\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
