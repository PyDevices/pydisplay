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

PyScript runs on asyncio. **`async`-tagged gallery demos** (`calculator`, `paint`, `eventsys_simpletest`, …) use `multimer.dual_main` / `run_forever_async`. **`all`-tagged demos** run blocking loops after you click **Run** — many now exit on `events.QUIT` via `runtime.quit_requested` or full `runtime.poll()` dispatch. See [PyScript asyncio guide](pyscript-asyncio.md).

## Gallery examples (2026-06)

Regenerate the card list with `python scripts/pyscript_gen_packages.py`. Current gallery: **6 async**, **42 all** (48 total). Highlights:

| Script | Tag | Notes |
|--------|-----|-------|
| `calculator.py` | async | Best starting point |
| `paint.py` | async | Used by `web/pyscript/editor.html` |
| `eventsys_simpletest.py` | async | Minimal event loop |
| `pydisplay_demo_async.py` | async | Flagship showcase |
| `hello.py`, `scroll.py`, `displaysys_simpletest.py` | all | Quit-aware blocking loops |
| `chango`, `noto_fonts` | all | One-shot draws (package manifests) |

Binary-dependent demos are excluded via `# pyscript binaries:` in the example header. Use `# pyscript skip: gallery` to omit a demo from the card grid. See `scripts/pyscript_gen_packages.py`.

## Board config

`board_configs/psdisplay/` — 320×480 canvas with host input via `runtime`.

## Next

- [PyScript asyncio porting](pyscript-asyncio.md)
- [PyScript troubleshooting (agents)](../testing/pyscript-troubleshooting.md) — Playwright, hangs, multimer/WASM
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
