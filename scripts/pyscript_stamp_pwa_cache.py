#!/usr/bin/env python3
"""Stamp ``CACHE_NAME`` in the PWA service worker from a shell content hash.

Only the precached shell assets listed in ``sw.js`` (``STATIC_ASSETS``) plus the
service-worker source itself (with a stable ``CACHE_NAME`` placeholder) feed the
hash. Example / ``src/`` / packages churn does **not** change the cache id, so
installed PWAs are not prompted to update on every Pages deploy.

Usage::

    # Deploy (after assembling _site/pyscript):
    python scripts/pyscript_stamp_pwa_cache.py _site/pyscript

    # Local check (writes into web/pyscript — usually skip; leave -dev):
    python scripts/pyscript_stamp_pwa_cache.py web/pyscript --check

Deploy stamps a short hash; source in git keeps ``pydisplay-pwa-dev``.

When ``sw.js`` contains ``MIGRATION: cache-purge`` (one-deploy cache purge for
legacy installs), stamping is skipped. See ``docs/guides/pyscript-pwa.md``
(Orphaned service workers and cache migration).
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_NAME_RE = re.compile(r"""(const\s+CACHE_NAME\s*=\s*['"])([^'"]+)(['"]\s*;)""")
STATIC_ASSETS_RE = re.compile(
    r"const\s+STATIC_ASSETS\s*=\s*\[(.*?)\];",
    re.DOTALL,
)
ASSET_STRING_RE = re.compile(r"""['"](\./[^'"]+)['"]""")
PLACEHOLDER_CACHE = "pydisplay-pwa-__SHELL_HASH__"
MIGRATION_MARKER = "MIGRATION: cache-purge"
# Gallery cards churn on many pushes; strip generated demos so they don't force
# installed PWAs to prompt. Stale-while-revalidate still refreshes index.html.
GEN_DEMOS_RE = re.compile(
    r"<!-- GEN:demos:start -->.*?<!-- GEN:demos:end -->",
    re.DOTALL,
)


def parse_static_assets(sw_text: str) -> list[str]:
    m = STATIC_ASSETS_RE.search(sw_text)
    if not m:
        raise SystemExit("sw.js: missing STATIC_ASSETS array")
    assets = ASSET_STRING_RE.findall(m.group(1))
    if not assets:
        raise SystemExit("sw.js: STATIC_ASSETS is empty")
    return assets


def normalize_sw_for_hash(sw_text: str) -> str:
    """Replace CACHE_NAME value so the stamp does not circularly hash itself."""
    if not CACHE_NAME_RE.search(sw_text):
        raise SystemExit("sw.js: missing const CACHE_NAME = '…';")
    return CACHE_NAME_RE.sub(
        rf"\g<1>{PLACEHOLDER_CACHE}\g<3>",
        sw_text,
        count=1,
    )


def asset_bytes_for_hash(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix.lower() in {".html", ".htm"}:
        text = raw.decode("utf-8")
        text = GEN_DEMOS_RE.sub(
            "<!-- GEN:demos:start -->\n            <!-- GEN:demos:end -->",
            text,
            count=1,
        )
        return text.encode("utf-8")
    return raw


def shell_hash(pyscript_dir: Path) -> str:
    sw_path = pyscript_dir / "sw.js"
    if not sw_path.is_file():
        raise SystemExit(f"missing {sw_path}")
    sw_text = sw_path.read_text(encoding="utf-8")
    assets = parse_static_assets(sw_text)

    h = hashlib.sha256()
    # Normalized SW body first (logic changes bump the id even if assets match).
    h.update(normalize_sw_for_hash(sw_text).encode("utf-8"))
    h.update(b"\0")

    for rel in assets:
        path = pyscript_dir / rel.removeprefix("./")
        if not path.is_file():
            raise SystemExit(f"STATIC_ASSETS entry missing: {rel} ({path})")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(asset_bytes_for_hash(path))
        h.update(b"\0")

    return h.hexdigest()[:12]


def is_migration_sw(sw_text: str) -> bool:
    return MIGRATION_MARKER in sw_text


def stamp(pyscript_dir: Path, *, check: bool) -> str:
    sw_path = pyscript_dir / "sw.js"
    sw_text = sw_path.read_text(encoding="utf-8")
    if is_migration_sw(sw_text):
        print("migration sw.js — skipping CACHE_NAME stamp")
        return "migration"
    digest = shell_hash(pyscript_dir)
    cache_name = f"pydisplay-pwa-{digest}"
    new_text, n = CACHE_NAME_RE.subn(
        rf"\g<1>{cache_name}\g<3>",
        sw_text,
        count=1,
    )
    if n != 1:
        raise SystemExit("sw.js: failed to stamp CACHE_NAME")
    if new_text == sw_text:
        print(f"CACHE_NAME already {cache_name}")
        return cache_name
    if check:
        print(f"would stamp CACHE_NAME={cache_name}")
        return cache_name
    sw_path.write_text(new_text, encoding="utf-8")
    try:
        shown = sw_path.relative_to(REPO_ROOT)
    except ValueError:
        shown = sw_path
    print(f"stamped {shown} → {cache_name}")
    return cache_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pyscript_dir",
        type=Path,
        help="Directory containing sw.js and STATIC_ASSETS (e.g. _site/pyscript)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compute/print the cache name without writing",
    )
    args = parser.parse_args(argv)
    pyscript_dir = args.pyscript_dir
    if not pyscript_dir.is_absolute():
        pyscript_dir = (Path.cwd() / pyscript_dir).resolve()
    stamp(pyscript_dir, check=args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
