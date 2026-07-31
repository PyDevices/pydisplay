"""Static contracts for the gallery's embedded demo workspace."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "pyscript" / "index.html"
CSS = ROOT / "web" / "pyscript" / "site.css"
DEMO_CSS = ROOT / "web" / "pyscript" / "demo.css"
THEME = ROOT / "web" / "pyscript" / "theme-toggle.js"
RUNTIME_LAYOUT = ROOT / "web" / "pyscript" / "runtime-layout.js"


def test_gallery_has_sidebar_and_single_demo_frame():
    source = INDEX.read_text(encoding="utf-8")
    assert 'class="gallery-workspace"' in source
    assert 'class="gallery-sidebar"' in source
    assert source.count('id="demo-frame"') == 1
    assert 'class="gallery-preview-bar"' not in source
    assert "Selected demo</span>" not in source


def test_every_generated_demo_runtime_can_be_embedded():
    source = INDEX.read_text(encoding="utf-8")
    generated = source.split("<!-- GEN:demos:start -->", 1)[1].split("<!-- GEN:demos:end -->", 1)[
        0
    ]
    loader_pages = {
        href.split("?", 1)[0] for href in re.findall(r'<a class="go" href="([^"]+)"', generated)
    }
    allowed = set(re.findall(r"'([^']+\.html)': true", source.split("var allowedPages =", 1)[1]))
    assert loader_pages <= allowed


def test_selection_is_bookmarkable_and_preserves_modifier_clicks():
    source = INDEX.read_text(encoding="utf-8")
    assert "parent.searchParams.set('run', selected.relative)" in source
    assert "window.history.pushState" in source
    assert "window.addEventListener('popstate'" in source
    assert "event.metaKey" in source
    assert "event.ctrlKey" in source


def test_gallery_layout_keeps_sidebar_beside_preview_until_mobile():
    css = CSS.read_text(encoding="utf-8")
    assert "grid-template-columns: minmax(300px, 1fr) fit-content(100%);" in css
    assert "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));" in css
    assert ".gallery-sidebar" in css
    assert ".gallery-preview" in css
    assert "@media (max-width: 900px)" in css


def test_runtime_loaders_show_two_cards_and_autorun():
    for name in ("micropython.html", "pyodide.html"):
        source = (ROOT / "web" / "pyscript" / name).read_text(encoding="utf-8")
        assert 'class="runtime-page"' in source
        assert 'id="run-btn"' not in source
        assert 'class="device"' in source
        assert 'class="console-panel"' in source
        assert "def _start():" in source
        assert "            _start()" in source
        assert 'addEventListener("click"' not in source


def test_gallery_uses_local_theme_toggle_and_syncs_the_frame():
    source = INDEX.read_text(encoding="utf-8")
    theme = THEME.read_text(encoding="utf-8")
    assert '<script src="./theme-toggle.js" defer></script>' in source
    assert "applyThemeToFrames(next)" in theme
    assert 'document.querySelectorAll("iframe")' in theme


def test_runtime_frame_and_sidebar_follow_content_height():
    source = INDEX.read_text(encoding="utf-8")
    layout = RUNTIME_LAYOUT.read_text(encoding="utf-8")
    assert 'scrolling="no"' in source
    assert "frame.style.height = Math.ceil(height) + 'px'" in source
    assert "frame.style.width = width + 'px'" in source
    assert "sidebar.style.height = !mobile && height > 0" in source
    assert 'panel.style.width = width + "px"' in layout
    assert 'panel.style.height = height + "px"' in layout
    assert "width: width" in layout


def test_runtime_cards_use_compact_outer_padding():
    css = DEMO_CSS.read_text(encoding="utf-8")
    assert "padding: 6px 8px 16px;" in css
    assert "padding: 16px 9px 6px;" in css
    assert "padding-top: 0;" in css
    assert "padding-bottom: 0;" in css


def test_standalone_runtime_uses_side_by_side_height_tracking():
    css = DEMO_CSS.read_text(encoding="utf-8")
    layout = RUNTIME_LAYOUT.read_text(encoding="utf-8")
    assert ".runtime-page.runtime-standalone .play-area" in css
    assert "grid-template-columns: auto auto;" in css
    assert "var standalone = window.parent === window;" in layout
    assert "if (lastWidth < 0)" in layout
    assert "if (height !== lastHeight)" in layout


def test_console_is_opt_in_and_gallery_enables_it():
    index = INDEX.read_text(encoding="utf-8")
    layout = RUNTIME_LAYOUT.read_text(encoding="utf-8")
    for name in ("micropython.html", "pyodide.html"):
        source = (ROOT / "web" / "pyscript" / name).read_text(encoding="utf-8")
        assert 'class="console-panel" aria-label="Console output" hidden' in source
    assert 'get("console") === "true"' in layout
    assert "url.searchParams.set('console', 'true')" in index
    assert "frame.src = iframeUrl(selected.relative)" in index
