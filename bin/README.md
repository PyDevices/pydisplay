# Prebuilt runtime binaries

Committed copies of the desktop MicroPython/CircuitPython (and Windows
MicroPython, for completeness) unix executables built with pydisplay's
required native modules (notably [graphics](https://github.com/PyDevices/graphics)).
They exist so that environments without a local firmware build — most
importantly **Cursor Cloud agents** — can run the example test matrix without
compiling MicroPython/CircuitPython from source.

| File | Runtime | Used by |
|------|---------|---------|
| `micropython` | MicroPython unix (linux x86_64) | `micropython` runtime |
| `circuitpython` | CircuitPython unix (linux x86_64) | `circuitpython` runtime |
| `micropython.exe` | MicroPython Windows (.exe) | **not used by cloud agents** — committed for completeness only; Windows binaries cannot run in the Cursor Cloud (Linux) sandbox |

`tools/example_runtimes.toml` resolves each runtime via `PATH`, then
`~/bin/<name>` (local override), then falls back to
`repo:bin/<name>` (this directory) — so this is transparent to local
development and only matters where the first two aren't available.

Rebuild from a sibling workspace (`micropython/` + `graphics/`, and for CP
`circuitpython/` + patches as in [usdl2](https://github.com/PyDevices/usdl2) /
[lv_circuitpython_mod](https://github.com/PyDevices/lv_circuitpython_mod)
docs), then re-copy the binaries here whenever the `graphics` cmod or
port config changes in a way that affects these executables.
([cmods](https://github.com/PyDevices/cmods) `./build_mp.sh` /
`lv_circuitpython_mod/build_cp.sh` are optional convenience wrappers.)
