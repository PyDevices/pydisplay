# PyScript local development

**Who:** You run or hack the browser demo locally, or port examples to PyScript.

**Prerequisites:** Python 3 on your PC (for `http.server` only).

## Live demo (online)

[PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/)

| Page | URL |
|------|-----|
| Calculator | [demo/html/?modules=calculator](https://PyDevices.github.io/pydisplay/demo/html/?modules=calculator) |
| Test runner | [demo/html/test.html](https://PyDevices.github.io/pydisplay/demo/html/test.html) |
| REPL | [demo/html/repl.html](https://PyDevices.github.io/pydisplay/demo/html/repl.html) |
| Editor | [demo/html/editor.html](https://PyDevices.github.io/pydisplay/demo/html/editor.html) |

## Run locally

--8<-- "_snippets/pyscript-local.md"

Examples in the [browser gallery](https://PyDevices.github.io/pydisplay/demo/) are copied to the deploy site and installed from the same origin on GitHub Pages. Locally, `tools/serve.py` serves your working tree — gallery pages load `src/examples/` via `html/?modules=…`. Non-gallery pages (`repl.html`, `editor.html`) may still use `github:` installs.

## asyncio requirement

PyScript runs on asyncio. **`async`-tagged gallery demos** (`calculator`, `paint`, `eventsys_simpletest`, …) use `multimer.dual_main` / `run_forever_async`. **`all`-tagged demos** run blocking loops after you click **Run** — many now exit on `events.QUIT` via `poll_quit_discarding_others(broker)` or full `broker.poll()` dispatch. See [PyScript asyncio guide](pyscript-asyncio.md).

## Gallery examples (2026-06)

Regenerate the card list with `python tools/gen_demo_pages.py`. Current gallery: **6 async**, **42 all** (48 total). Highlights:

| Script | Tag | Notes |
|--------|-----|-------|
| `calculator.py` | async | Best starting point |
| `paint.py` | async | Used by `html/editor.html` |
| `eventsys_simpletest.py` | async | Minimal event loop |
| `pydisplay_demo_async.py` | async | Flagship showcase |
| `hello.py`, `scroll.py`, `displaysys_simpletest.py` | all | Quit-aware blocking loops |
| `chango`, `noto_fonts` | all | One-shot draws (package manifests) |

Binary-dependent demos are excluded via `# pyscript binaries:` in the example header. Use `# pyscript skip: gallery` to omit a demo from the card grid. See `tools/gen_demo_pages.py`.

## Board config

`board_configs/psdisplay/` — 320×480 canvas with touch broker.

## Next

- [PyScript asyncio porting](pyscript-asyncio.md)
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
