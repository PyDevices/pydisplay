# PyScript

Experimental browser support via [PyScript](https://pyscript.net/) and `displaysys.psdisplay.PSDisplay`.

**Quick start:** [PyScript guide](../guides/pyscript.md) and [Try pydisplay](../try/index.md).

**Asyncio porting:** [PyScript asyncio guide](../guides/pyscript-asyncio.md).

!!! warning "Work in progress"
    PyScript support is experimental. Only touchscreen input is implemented. Most examples use blocking loops and **will not run** in the browser until ported to asyncio.

## Board config

`board_configs/psdisplay/board_config.py` — 320×480 canvas with touch broker.

## Contributing

Pull requests welcome for `displaysys/psdisplay.py`, asyncio example ports, and files under `html/`.
