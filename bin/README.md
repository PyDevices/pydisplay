# Prebuilt runtime binaries

Committed copies of the desktop MicroPython/CircuitPython (and Windows
MicroPython, for completeness) unix executables built from
[`~/github/cmods`](https://github.com/PyDevices) with all of pydisplay's
required native modules (notably `graphics`). They exist so that environments
without a local `~/github/cmods` checkout — most importantly **Cursor Cloud
agents** — can run the example test matrix without needing to build
MicroPython/CircuitPython from source.

| File | Runtime | Used by |
|------|---------|---------|
| `micropython` | MicroPython unix (linux x86_64) | `micropython` runtime |
| `circuitpython` | CircuitPython unix (linux x86_64) | `circuitpython` runtime |
| `micropython.exe` | MicroPython Windows (.exe) | **not used by cloud agents** — committed for completeness only; Windows binaries cannot run in the Cursor Cloud (Linux) sandbox |

`tools/example_runtimes.toml` resolves each runtime via `PATH`, then
`~/bin/<name>` (Brad's local dev machine), then falls back to
`repo:bin/<name>` (this directory) — so this is transparent to local
development and only matters where the first two aren't available.

Rebuild upstream from `~/github/cmods` (see that repo's `AGENTS.md` and
`graphics/PUBLISHING.md`) and re-copy here whenever the `graphics` cmod or
MicroPython/CircuitPython port config changes in a way that affects these
binaries.
