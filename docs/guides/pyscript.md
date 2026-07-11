# PyScript local development

**Who:** You run or hack the browser demo locally, or port examples to PyScript.

**Prerequisites:** Python 3 on your PC (for `http.server` only).

## Live demo (online)

[PyDevices.github.io/pydisplay/pyscript/](https://PyDevices.github.io/pydisplay/pyscript/)

| Page | URL |
|------|-----|
| Calculator | [pyscript/load.html?modules=calculator](https://PyDevices.github.io/pydisplay/pyscript/load.html?modules=calculator) |
| Test runner | [pyscript/test.html](https://PyDevices.github.io/pydisplay/pyscript/test.html) |
| REPL | [pyscript/repl.html](https://PyDevices.github.io/pydisplay/pyscript/repl.html) |
| Editor | [pyscript/editor.html](https://PyDevices.github.io/pydisplay/pyscript/editor.html) |

## Run locally

--8<-- "_snippets/pyscript-local.md"

Examples in the [browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) are copied to the deploy site and installed from the same origin on GitHub Pages. Locally, `tools/serve.py` serves your working tree — gallery pages load `src/examples/` via `web/pyscript/load.html?modules=…`. Non-gallery pages (`repl.html`, `editor.html`) may still use `github:` installs.

## asyncio requirement

PyScript runs on asyncio. Prefer `multimer.loop.run_forever` / `dual_main` so demos yield to the event loop in the browser. See [PyScript asyncio guide](pyscript-asyncio.md).

## Gallery examples

Regenerate the card list with `python scripts/pyscript_gen_packages.py`. Every example entry under `src/examples/` is included by default.

| Marker | Effect |
|--------|--------|
| `# pyscript skip: gallery` | Omit from the card grid |
| `# pyscript featured` | Pin to the top (badge) |
| `# pyscript modules: …` | Extra modules to install with the entry |
| `# pyscript packages: …` | Pre-install repo-root mip packages (e.g. `micropython-nano-gui`) into `/add_ons` before import |

Hinch GUI smokes (`nano_gui_simpletest`, `micro_gui_simpletest`, `touch_gui_simpletest`) use `# pyscript packages:` so the loader downloads one `gui/` tree via `github:PyDevices/pydisplay/packages/…` before the example imports. First open needs network; later loads in the same session reuse the VFS until reload.

Featured starters: `pydisplay_demo`, `testris`. See `scripts/pyscript_gen_packages.py` and [examples catalog](../examples/index.md#pyscript-gallery-markers).

## Board config

`board_configs/psdisplay/` — 320×480 canvas with host input via `runtime`.

## Next

- [PyScript asyncio porting](pyscript-asyncio.md)
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
