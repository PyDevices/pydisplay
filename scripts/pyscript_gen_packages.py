#!/usr/bin/env python3
"""
pyscript_gen_packages.py — refresh the pydisplay PyScript browser gallery.

Default-includes every example **entry point** under ``src/examples/``:

  - ``examples/<name>.py`` — single-file module
  - ``examples/<name>/<name>.py`` — package (preferred over ``__init__.py``)
  - ``examples/<name>/__init__.py`` — package when no ``<name>.py`` entry

Opt out with ``# pyscript skip: gallery`` in the first 10 lines.

Optional headers (first 10 lines):

  - ``# pyscript featured`` — pin card to the top of the gallery (badge)
  - ``# pyscript modules:`` — extra ``examples/``-relative module stems for
    multi-module loaders (e.g. ``calc_engine``)
  - ``# pyscript packages:`` — repo-root mip package stems (e.g.
    ``micropython-nano-gui``) pre-installed into ``/add_ons`` before import
  - ``# pyscript skip: gallery`` — omit from the browser card grid

Then:

  - Updates gallery cards in ``web/pyscript/index.html`` (``GEN:demos`` markers)
  - Writes ``web/pyscript/<name>.json`` MIP manifests for package examples
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

MIP_MANIFEST_VERSION = "0.0.5"

KEEP_HTML = frozenset({"index", "load", "repl", "editor", "test", "embed"})
LOADER_BASE = "load.html"

ARROW = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)

GENERIC_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>'
)

HEADER_SCAN_LINES = 10

LOCAL_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.MULTILINE,
)


class Example:
    """One browser-gallery demo discovered from ``src/examples/``."""

    def __init__(self, name: str, source_rel: str, kind: str):
        self.name = name
        self.source_rel = source_rel
        self.kind = kind  # "module" | "manifest"
        self.docstring_blurb = ""
        self.pyscript_files: list[str] = []
        self.pyscript_packages: list[str] = []
        self.featured = False

    @property
    def title(self) -> str:
        return self.name.replace("_", " ").title()

    @property
    def blurb(self) -> str:
        return (
            self.docstring_blurb
            or f"The <code>{self.name}</code> demo running in the browser via PyScript."
        )

    def loader_href(self, base: str = LOADER_BASE) -> str:
        if self.kind == "module":
            stems = ",".join(Path(path).stem for path in self.pyscript_files)
            href = f"{base}?modules={stems}"
        else:
            href = f"{base}?manifests={self.name}"
        if self.pyscript_packages:
            href += f"&packages={','.join(self.pyscript_packages)}"
        return href


def parse_header_list(lines: list[str], prefix: str) -> list[str]:
    for line in lines[:HEADER_SCAN_LINES]:
        s = line.strip()
        if s.startswith(prefix):
            body = s.split(":", 1)[1].strip()
            return [part.strip() for part in body.split(",") if part.strip()]
    return []


def header_has_featured(lines: list[str]) -> bool:
    for line in lines[:HEADER_SCAN_LINES]:
        s = line.strip()
        if s == "# pyscript featured" or s.startswith("# pyscript featured:"):
            return True
    return False


def skip_gallery(lines: list[str]) -> bool:
    return "gallery" in parse_header_list(lines, "# pyscript skip:")


def _py_sort_key(rel: str) -> tuple:
    parts = rel.split("/")
    name = parts[-1]
    init_first = 0 if name == "__init__.py" else 1
    return (parts[:-1], init_first, name)


def discover_package_py_files(name: str) -> list[str]:
    pkg_dir = EXAMPLES_DIR / name
    if not pkg_dir.is_dir():
        raise SystemExit(f"examples/{name}: package directory missing")
    paths: list[str] = []
    for path in sorted(pkg_dir.rglob("*.py")):
        rel = path.relative_to(EXAMPLES_DIR).as_posix()
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
) -> list[str]:
    extra_modules = parse_header_list(lines, "# pyscript modules:")
    entry_rel = path.relative_to(EXAMPLES_DIR).as_posix()

    if kind == "manifest":
        return discover_package_py_files(name)

    py_files = [entry_rel]
    py_files.extend(discover_local_py_imports(path, text))
    for raw in extra_modules:
        rel = normalize_py_path(raw)
        if rel not in py_files:
            py_files.append(rel)
    return finalize_py_files(py_files, entry_rel)


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


def classify_entry(path: Path) -> tuple[str, str] | None:
    """Return ``(name, kind)`` for a gallery entry path, or None if not an entry."""
    try:
        rel = path.relative_to(EXAMPLES_DIR)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) == 1 and parts[0].endswith(".py"):
        return path.stem, "module"
    if len(parts) == 2 and parts[1] == f"{parts[0]}.py":
        return parts[0], "manifest"
    if len(parts) == 2 and parts[1] == "__init__.py":
        return parts[0], "manifest"
    return None


def entry_priority(path: Path) -> int:
    """Lower sorts first: ``<name>.py`` preferred over ``__init__.py`` for packages."""
    if path.name == "__init__.py":
        return 1
    return 0


def parse_example(path: Path) -> Example | None:
    classified = classify_entry(path)
    if classified is None:
        return None
    name, kind = classified

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if skip_gallery(lines):
        return None

    rel = path.relative_to(REPO_ROOT).as_posix()
    ex = Example(name, rel, kind)
    ex.featured = header_has_featured(lines)
    ex.docstring_blurb = extract_blurb(text, name)
    ex.pyscript_files = resolve_pyscript_paths(path, kind, name, lines, text)
    ex.pyscript_packages = parse_header_list(lines, "# pyscript packages:")
    for entry in ex.pyscript_files:
        if not (EXAMPLES_DIR / entry).is_file():
            raise SystemExit(f"{rel}: missing pyscript file {entry}")
    return ex


def _is_personal_example(path: Path) -> bool:
    try:
        rel = path.relative_to(EXAMPLES_DIR)
    except ValueError:
        return False
    return bool(rel.parts) and rel.parts[0] in PERSONAL_EXAMPLE_DIRS


def example_py_files() -> list[Path]:
    """Candidate entry ``*.py`` under ``src/examples/``, excluding personal trees."""
    paths: list[Path] = []
    seen: set[str] = set()
    for path in sorted(EXAMPLES_DIR.rglob("*.py")):
        if _is_personal_example(path):
            continue
        if classify_entry(path) is None:
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
                if classify_entry(path) is None:
                    continue
                key = str(path)
                if key not in seen:
                    paths.append(path)
                    seen.add(key)
    return paths


def discover() -> list[Example]:
    """One Example per name; prefer ``<name>.py`` over ``__init__.py``.

    If the preferred entry is skipped, the package is omitted (do not fall back
    to ``__init__.py`` when ``<name>.py`` exists but opts out).
    """
    by_name: dict[str, list[Path]] = {}
    for path in example_py_files():
        classified = classify_entry(path)
        if classified is None:
            continue
        name, _kind = classified
        by_name.setdefault(name, []).append(path)

    found: list[Example] = []
    for name, paths in sorted(by_name.items()):
        named = [p for p in paths if p.name == f"{name}.py"]
        primary = named[0] if named else sorted(paths, key=entry_priority)[0]
        ex = parse_example(primary)
        if ex:
            found.append(ex)
    return found


def example_mip_manifest(ex: Example) -> dict:
    return {
        "urls": [[path, f"./src/examples/{path}"] for path in ex.pyscript_files],
        "version": MIP_MANIFEST_VERSION,
    }


def render_card(ex: Example, base: str = LOADER_BASE) -> str:
    tag = (
        '\n                        <span class="tag featured">featured</span>'
        if ex.featured
        else ""
    )
    return f'''                <a class="card" href="{ex.loader_href(base)}">
                    <div class="card-top">
                        <span class="card-icon">{GENERIC_ICON}</span>{tag}
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
        # Leave non-gallery JSON alone (e.g. vendor locks) — only remove known
        # stale *example* manifests that we previously wrote. Heuristic: only
        # delete if the stem looks like an example package we no longer emit.
        # Safer: only delete JSON that were in keep's previous set by checking
        # they are simple MIP manifests with urls pointing at src/examples.
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        urls = data.get("urls")
        if not isinstance(urls, list) or not urls:
            continue
        first = urls[0]
        if not (
            isinstance(first, list) and len(first) >= 2 and "./src/examples/" in str(first[1])
        ):
            continue
        rel = str(path.relative_to(REPO_ROOT))
        if check:
            stale.append(rel)
            continue
        path.unlink()
        print(f"removed {rel}")


def remove_stale_demo_html(stale: list[str], check: bool) -> None:
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

    examples = sorted(discover(), key=lambda e: (not e.featured, e.title.lower()))
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
    # Migrate old dual markers if still present.
    if "<!-- GEN:demos:start -->" not in index_text:
        raise SystemExit(
            f"{INDEX.name} is missing <!-- GEN:demos:start --> "
            "(collapse async/all sections before regenerating)"
        )
    index_text = replace_block(index_text, "demos", render_cards(examples))
    write(INDEX, index_text)

    n_module = sum(1 for ex in examples if ex.kind == "module")
    n_manifest = sum(1 for ex in examples if ex.kind == "manifest")
    n_featured = sum(1 for ex in examples if ex.featured)
    print(
        f"\n{len(examples)} gallery demo(s) "
        f"({n_module} module, {n_manifest} manifest; {n_featured} featured)."
    )
    if args.check and stale:
        print("STALE:\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
