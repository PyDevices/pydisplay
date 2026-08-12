# `bin/` — runtimes and launchers

## Launchers

| Script | Role |
|--------|------|
| [`pyscript.sh`](pyscript.sh) | Local PyScript gallery / demo server (`./bin/pyscript.sh …`) |
| [`jupyter.sh`](jupyter.sh) | JupyterLab / Cursor notebooks (`./bin/jupyter.sh …`) |
| [`android.sh`](android.sh) | Thin shim → [`pydevices-android-template/scripts/android.sh`](../../pydevices-android-template/scripts/android.sh) (prefer `~/bin/android.sh` on PATH) |

Supporting Python still lives under `tools/` (e.g. `tools/serve.py`, `tools/pyscript_autotest.py`).

## Prebuilt runtime binaries

Committed copies of the desktop MicroPython/CircuitPython (and Windows
MicroPython, for completeness) unix executables built with pydevices-examples's
required native modules (notably [pygraphics](https://github.com/PyDevices/pygraphics)).
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

Rebuild and reinstall whenever a usermod or port config that links into these
executables changes. From a local [cmods](https://github.com/PyDevices/cmods)
workspace (optional convenience):

```bash
../cmods/build_runtimes.sh
```

That installs into the workspace `bin/` first, then (when this repo is a sibling
of that workspace) also refreshes this directory plus
`web/pyscript/vendor/micropython/` (wasm). Without that workspace, build from a
sibling layout (`micropython/` + `pygraphics/`, and for CP `circuitpython/` +
[lvgl-circuitpython](https://github.com/PyDevices/lvgl-circuitpython)
as needed), then copy here — rename the CircuitPython unix binary to `circuitpython`.
