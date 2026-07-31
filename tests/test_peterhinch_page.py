"""Static contract tests for the dynamic Peter Hinch demo browser."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web" / "pyscript" / "peterhinch.html"


def _source():
    return PAGE.read_text(encoding="utf-8")


def _excluded(gui):
    source = _source()
    match = re.search(
        rf'    "{gui}": \{{(?P<body>.*?)\n    \}},',
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    return set(re.findall(r'^\s+"([^"]+)",', match.group("body"), flags=re.MULTILINE))


def test_page_is_micropython_only_and_uses_existing_config():
    source = _source()
    assert '<script type="mpy" config="./micropython.toml"' in source
    assert "pyodide" not in source.lower()


def test_dynamic_discovery_is_sorted_and_excludes_init():
    source = _source()
    assert 'os.listdir("/add_ons/gui/demos")' in source
    assert 'filename != "__init__.py"' in source
    assert "names.sort()" in source


def test_display_size_is_overridden_before_setup_import():
    source = _source()
    width = source.index('env_set("PYDISPLAY_WIDTH", 320)')
    height = source.index('env_set("PYDISPLAY_HEIGHT", 240)')
    setup_import = source.index("__import__(setup)")
    assert width < setup_import
    assert height < setup_import


def test_micro_gui_has_visible_keyboard_hint():
    source = _source()
    assert "Use the arrow keys to navigate and adjust. Press Space to select." in source
    assert "document.getElementById('control-hint').hidden = gui !== 'micro';" in source


def test_known_incompatible_demos_are_filtered():
    assert _excluded("nano") == {
        "aclock",
        "aclock_large",
        "aclock_ttgo",
        "alevel",
        "asnano",
        "asnano_sync",
        "clock_batt",
        "clocktest",
        "color15",
        "color96",
        "epd21_sync",
        "epd29_async",
        "epd29_lowpower",
        "epd29_sync",
        "epd_async",
        "fpt",
        "mono_test",
        "sharptest",
    }
    assert _excluded("micro") == {"audio", "bitmap", "date", "epaper", "qrcode"}
    assert _excluded("touch") == {"audio", "bitmap", "date", "qrcode"}


def test_selected_demo_must_be_discovered_and_supported():
    source = _source()
    assert "if selected not in names:" in source
    assert "if selected in discovered:" in source
    assert "Demo is not compatible with the browser runtime:" in source
    assert '__import__("gui.demos." + selected)' in source


def test_gallery_regeneration_preserves_page():
    generator = (ROOT / "scripts" / "gallery_generator.py").read_text(encoding="utf-8")
    keep_html = generator.split("KEEP_HTML =", 1)[1].split("ARROW =", 1)[0]
    assert '"peterhinch"' in keep_html
