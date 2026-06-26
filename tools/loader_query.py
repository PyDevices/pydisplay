"""Validate ``?modules=`` / ``?manifests=`` query values for html/index.html."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, urlparse

# Python identifier — matches every gallery example stem (calculator, noto_fonts, …).
SAFE_LOADER_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
LOADER_QUERY_KEYS = ("modules", "manifests")


def _normalize_stem(raw: str) -> str:
    name = raw.strip()
    if name.lower().endswith(".py"):
        name = name[:-3].strip()
    return name


def invalid_loader_names(query: str) -> list[str]:
    """Return unsafe names from ``modules`` / ``manifests`` query values."""
    if not query:
        return []
    qs = parse_qs(query, keep_blank_values=True)
    bad: list[str] = []
    for key in LOADER_QUERY_KEYS:
        for raw in qs.get(key, []):
            for part in raw.split(","):
                name = _normalize_stem(part)
                if not name:
                    continue
                if not SAFE_LOADER_NAME.match(name):
                    bad.append(name)
    return bad


def loader_query_error(query: str) -> str | None:
    bad = invalid_loader_names(query)
    if not bad:
        return None
    shown = ", ".join(repr(name) for name in bad)
    return f"Unsafe ?modules= / ?manifests= value(s): {shown}"


def loader_index_path(path: str) -> bool:
    """True if ``path`` is the parametric loader (ignoring query string)."""
    return urlparse(path).path.rstrip("/") == "/html/index.html"


def render_bad_request_html(detail: str) -> str:
    safe = html.escape(detail, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>400 Bad Request — pydisplay demo</title>
    <link rel="stylesheet" href="./demo.css">
</head>
<body>
    <header class="site-header">
        <div class="wrap">
            <a class="brand" href="../index.html">
                <span class="logo"><svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg></span>
                py<span class="accent">display</span>
            </a>
        </div>
    </header>
    <main class="wrap example-main">
        <h1>400 Bad Request</h1>
        <p>{safe}</p>
        <p><code>?modules=</code> and <code>?manifests=</code> names must be simple identifiers
        (letters, digits, underscore; no slashes or dots).</p>
        <p><a class="btn" href="../index.html">Back to demos</a></p>
    </main>
</body>
</html>
"""
