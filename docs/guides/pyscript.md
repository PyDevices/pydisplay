# PyScript local development

**Who:** You run or hack the browser demo locally, or port examples to PyScript.

**Prerequisites:** Python 3 on your PC (for `http.server` only).

## Live demo (online)

[PyDevices.github.io/pydisplay/pyscript/](https://PyDevices.github.io/pydisplay/pyscript/)

| Page | URL |
|------|-----|
| Calculator | [pyscript/micropython.html?modules=calc_graphics,calc_engine](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=calc_graphics,calc_engine) |
| Simple | [pyscript/simple.html](https://PyDevices.github.io/pydisplay/pyscript/simple.html) |
| REPL | [pyscript/repl.html](https://PyDevices.github.io/pydisplay/pyscript/repl.html) |
| Pyodide (modules / manifests) | [pyscript/pyodide.html?modules=calc_graphics,calc_engine](https://PyDevices.github.io/pydisplay/pyscript/pyodide.html?modules=calc_graphics,calc_engine) · [manifests=chango](https://PyDevices.github.io/pydisplay/pyscript/pyodide.html?manifests=chango) |

## Run locally

--8<-- "_snippets/pyscript-local.md"

Examples in the [browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) are copied to the deploy site and installed from the same origin on GitHub Pages. Locally, `tools/serve.py` serves your working tree — gallery pages load `src/examples/` via `web/pyscript/micropython.html?modules=…` / `?manifests=…` (MicroPython). Use `web/pyscript/pyodide.html` with the same query shape for Pyodide smoke tests (MIP JSON under `packages/` via the `web/pyscript/packages` symlink; no `?packages=`); it is not wired into the gallery. Non-gallery pages (`repl.html`, `simple.html`) may still use `github:` installs.

## asyncio requirement

PyScript runs on asyncio. Prefer `runtime.run_forever()` with `on` / `on_tick`
callbacks so demos stay responsive. See [PyScript asyncio guide](pyscript-asyncio.md).

## Gallery examples

Regenerate the card list with `python scripts/gallery_generator.py`. Every example entry under `src/examples/` is included by default.

| Marker | Effect |
|--------|--------|
| `# deps: …` | Logical packages → `mip` / `wheels` via `url_maker` |
| `# modules: …` | Extra example `.py` stems |
| `# manifests: …` | Extra site-served demo bundles (`packages/<name>.json`) |
| `# gallery: featured` | Pin to the top (badge) |
| `# gallery: skip` | Omit from the card grid |
| `# gallery: binaries` | Omit (needs non-mip assets) |

Hinch GUI smokes (`nano_gui_simpletest`, `micro_gui_simpletest`, `touch_gui_simpletest`) rely on `fetch_ph_gui` from the matching setup module — no gallery package header. First open needs network; later loads in the same session reuse the VFS until reload.

Featured starters: `pydisplay_demo`, `testris`. See `scripts/gallery_generator.py` and [examples catalog](../examples/index.md#pyscript-gallery-markers).

## Board config

`board_configs/psdisplay/` — 320×480 canvas with host input via `runtime`.

## Next

- [Make your PyScript app a PWA](pyscript-pwa.md)
- [Where PWAs run](../platforms/pwa.md) — host matrix (desktop, Android, iOS, TVs)
- [PyScript asyncio porting](pyscript-asyncio.md)
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
