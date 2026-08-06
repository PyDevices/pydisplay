# PyScript local development

**Who:** You run or hack the browser demo locally, or port examples to PyScript.

**Prerequisites:** Python 3 on your PC (for `http.server` only).

## Live demo (online)

[PyDevices.github.io/pydisplay/pyscript/](https://PyDevices.github.io/pydisplay/pyscript/)

| Page | URL |
|------|-----|
| Calculator | [pyscript/micropython.html?modules=calc_graphics,calc_engine](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=calc_graphics,calc_engine) |
| Editor | [pyscript/editor.html](https://PyDevices.github.io/pydisplay/pyscript/editor.html) |
| REPL | [pyscript/repl.html](https://PyDevices.github.io/pydisplay/pyscript/repl.html) |
| Async | [pyscript/async.html](https://PyDevices.github.io/pydisplay/pyscript/async.html) |
| DOM | [pyscript/dom.html](https://PyDevices.github.io/pydisplay/pyscript/dom.html) |
| Pyodide (modules / manifests) | [pyscript/pyodide.html?modules=calc_graphics,calc_engine](https://PyDevices.github.io/pydisplay/pyscript/pyodide.html?modules=calc_graphics,calc_engine) · [manifests=chango](https://PyDevices.github.io/pydisplay/pyscript/pyodide.html?manifests=chango) |

## Run locally

--8<-- "_snippets/pyscript-local.md"

Examples in the [browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) are copied to the deploy site and installed from the same origin on GitHub Pages. Locally, `tools/serve.py` serves your working tree — gallery pages load `src/examples/` via `web/pyscript/micropython.html?modules=…` / `?manifests=…` (MicroPython). Use `web/pyscript/pyodide.html` with the same query shape for Pyodide smoke tests (MIP JSON under `packages/` via the `web/pyscript/packages` symlink; no `?packages=`); it is not wired into the gallery. Non-gallery pages (`repl.html`, `editor.html`, `async.html`, `dom.html`) may still use `github:` installs.

## Minimal teaching shells

These tiny pages sit beside the gallery loaders and each highlight one PyScript idea:

| Page | Feature |
|------|---------|
| [`editor.html`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/editor.html) | `type="mpy-editor"` with hidden `setup` + shared `env` — editable lesson + Run |
| [`repl.html`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/repl.html) | `terminal worker` + `code.interact` |
| [`async.html`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/async.html) | `async` / `await` animation that yields to the browser |
| [`dom.html`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/dom.html) | HTML button → Python via `create_proxy` |

### REPL: worker vs main thread

`repl.html` uses `<script type="mpy" … terminal worker>`. The `worker` attribute runs MicroPython off the page's main thread so:

- `input()` works inside the terminal (no browser `prompt()` dialog)
- Long-running or blocking REPL code does not freeze the tab UI

Without `worker`, a MicroPython terminal still works, but `input()` falls back to the browser's native dialog, and a tight loop can freeze the page. Prefer `worker` for REPL-style shells unless you have a specific reason to stay on the main thread.

Gallery loaders and the `async.html` / `dom.html` shells stay on the **main thread** because they drive the canvas and DOM listeners directly (same pattern as `micropython.html`).

## asyncio requirement

PyScript runs on asyncio. Prefer `runtime.run_forever()` with `on` / `on_tick`
callbacks so demos stay responsive. See [PyScript asyncio guide](pyscript-asyncio.md), or open [`async.html`](https://PyDevices.github.io/pydisplay/pyscript/async.html) for a minimal bouncing-square loop.

## Gallery examples

Regenerate the card list with `python scripts/gallery_generator.py`. Every example entry under `src/examples/` is included by default.

| Marker | Effect |
|--------|--------|
| `# deps: …` | Logical packages → `?deps=` via `url_maker` (MIP on MicroPython, micropip on Pyodide) |
| `# modules: …` | Extra example `.py` stems |
| `# manifests: …` | Extra site-served demo bundles (`packages/<name>.json`) |
| `# gallery: featured` | Pin to the top (badge) |
| `# gallery: skip` | Omit from the card grid |
| `# gallery: binaries` | Omit (needs non-mip assets) |

Hinch GUI smokes (`nano_gui_simpletest`, `micro_gui_simpletest`, `touch_gui_simpletest`) rely on `fetch_ph_gui` from the matching setup module — no gallery package header. First open needs network; later loads in the same session reuse the VFS until reload.

Featured starters: `pydisplay_demo`, `testris`. See `scripts/gallery_generator.py` and [examples catalog](../examples/index.md#pyscript-gallery-markers).

## Board config

`board_configs/psdisplay/` — 320×480 canvas with host input via `runtime`.

## Headless / CDP troubleshooting

Prefer Playwright helpers over poking the IDE browser when demos hang:

| Script | Purpose |
|--------|---------|
| [`tools/ps_debug.py`](../../tools/ps_debug.py) | CDP console + network probe for a harness/load URL |
| [`tools/ps_shot.py`](../../tools/ps_shot.py) | Timed screenshot with a hard kill if Chromium stalls |

```bash
python tools/serve.py   # separate terminal
.venv/bin/python tools/ps_debug.py \
  'http://127.0.0.1:8000/web/pyscript/harness.html?modules=calc_graphics,calc_engine&autotest=1' 20
```

**Common wedge:** sync `multimer.sleep_ms` (or other blocking sleep) on the
**main thread** often stalls `page.evaluate` and screenshots — the browser
never yields. Prefer `runtime.run_forever()` / async sleep patterns from the
[asyncio guide](pyscript-asyncio.md). Capture console/CDP output with
`ps_debug.py` before assuming a gallery or package map regression.

Matrix notes (serve.py, Playwright install, `needs_playwright`):
[tools/README.md — Example test matrix](../../tools/README.md#example-test-matrix).

## Next

- [Make your PyScript app a PWA](pyscript-pwa.md)
- [Where PWAs run](../platforms/pwa.md) — host matrix (desktop, Android, iOS, TVs)
- [PyScript asyncio porting](pyscript-asyncio.md)
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
