# PyScript local development

**Who:** You run or hack the browser demo locally, or port examples to PyScript.

**Prerequisites:** Python 3 on your PC (for `http.server` only).

## Live demo (online)

[PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/)

| Page | URL |
|------|-----|
| Calculator | [demo/html/index.html?script=calculator](https://PyDevices.github.io/pydisplay/demo/html/index.html?script=calculator) |
| Test runner | [demo/html/test.html](https://PyDevices.github.io/pydisplay/demo/html/test.html) |
| REPL | [demo/html/repl.html](https://PyDevices.github.io/pydisplay/demo/html/repl.html) |
| Editor | [demo/html/editor.html](https://PyDevices.github.io/pydisplay/demo/html/editor.html) |

## Run locally

--8<-- "_snippets/pyscript-local.md"

Examples are still fetched from GitHub at runtime via `mip.install` in the HTML pages — local edits to `src/examples/` do not appear until pushed (or you change the HTML). Library code under `src/lib/` and `src/add_ons/` is mounted from your working tree via `html/pyscript.toml`.

## asyncio requirement

PyScript runs on asyncio. Blocking `while True:` loops without `await` will hang the tab. See [PyScript asyncio guide](pyscript-asyncio.md).

## Compatible examples today

| Script | Notes |
|--------|-------|
| `calculator.py` | Best starting point |
| `paint.py` | Used by `html/editor.html` |
| `eventsys_simpletest.py` | Minimal event loop |
| `apollo.py` | Heavier demo |

## Board config

`board_configs/psdisplay/` — 320×480 canvas with touch broker.

## Next

- [PyScript asyncio porting](pyscript-asyncio.md)
- [Try pydisplay](../try/index.md)
- [Platform notes](../platforms/pyscript.md)

## Reference

- [API reference (core)](../reference/) → `displaysys.psdisplay`
