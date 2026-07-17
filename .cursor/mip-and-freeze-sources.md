# MIP install vs frozen manifest sources

Private reference (not for RTD). Verified 2026-07-08 against pydisplay, PyDevices/micropython-lib, and cmods.

## Quick answer

| Install path | Source | On device after install |
|--------------|--------|-------------------------|
| `mip.install("displaysys", index=PyDevices micropython-lib)` | micropython-lib MIP index | **`.mpy`** by default (matching bytecode version) |
| `mip.install("displaysys", index=..., mpy=False)` on device | same index, source channel | **`.py`** |
| `mpremote mip install --no-mpy --index … displaysys` | same index, `py/` channel | **`.py`** |
| `mip.install("github:PyDevices/pydisplay/packages/displaysys.json")` | GitHub repo manifests | **`.py`** (never `.mpy`) |
| `mip.install("github:PyDevices/pydisplay/src/lib/board_config.py")` | single GitHub file | **`.py`** |
| `cmods/build_mp.sh` → `FROZEN_MANIFEST` | local `.py` trees under cmods | **frozen bytecode** in firmware (not filesystem `.py`/`.mpy`) |

## pydisplay installer routing

[`installer.py`](../installer.py) wraps two paths:

| Function | Package name pattern | Default format |
|----------|---------------------|----------------|
| `lib_install()` | no `/` (e.g. `displaysys`, `eventsys`) | `.mpy` via micropython-lib index |
| `repo_install()` | contains `/` (e.g. `/packages/examples.json`) | `.py` from GitHub |
| `install()` | dispatches on `/` in name | same as above |

On host (not on-device MicroPython), `lib_install(..., mpy=False)` maps to `mpremote mip install --no-mpy`.

## micropython-lib MIP index (`.mpy` default, `.py` optional)

Published by [`scripts/publish_sync_packages.sh`](../scripts/publish_sync_packages.sh) into the PyDevices/micropython-lib `gh-pages` tree, compiled by [`scripts/build.py`](../scripts/build.py) (upstream micropython-lib `tools/build.py`).

For each package the build script writes **two** index entries:

- `package/{mpy_version}/{name}/latest.json` — hashes point at **compiled `.mpy`** blobs under `file/`
- `package/py/{name}/latest.json` — hashes point at **source `.py`** blobs under `file/`

`mip.install()` on a device selects the bytecode version matching the running firmware unless `mpy=False` / `--no-mpy` is used, in which case it pulls from the `py/` channel.

See also [installation/mip-micropython-lib.md](../docs/installation/mip-micropython-lib.md).

## GitHub MIP (always `.py`)

[`github:PyDevices/pydisplay/…`](../docs/installation/mip-github.md) installs copy manifest-listed **source `.py` files** directly. No mpy-cross step. Used for:

- `packages/*.json` (add_ons, examples, spibus, i80bus, board bundles)
- `board_configs/…/package.json`
- individual paths (`/src/lib/board_config.py`, drivers, etc.)

## `cmods/build_mp.sh` frozen manifest

[`build_mp.sh`](../../cmods/build_mp.sh) passes `FROZEN_MANIFEST` (default: `cmods/manifest.py`) to MicroPython `make`. That is **not** MIP — nothing is downloaded at runtime.

### What `cmods/manifest.py` includes

1. **`my-manifest.py`** (optional, same directory) — not present in the default tree; hook for local overrides.
2. **`package("graphics", base_path="graphics/py", opt=3)`** — all `.py` under [`cmods/graphics/py/`](../../cmods/graphics/py/), compiled with **`-O3`** and **frozen into firmware** as bytecode (not left as `.py` or loose `.mpy` on the filesystem).
3. **`lv_micropython_cmod/manifest.py`** (if present) — LVGL bindings/modules for freeze.
4. **Port/board manifests** from the MicroPython tree (first match):
   - `$(PORT_DIR)/variants/pyscript/manifest.py`
   - `$(BOARD_DIR)/manifest.py`
   - `$(PORT_DIR)/boards/manifest.py`
   - `$(PORT_DIR)/variants/standard/manifest.py`
   - other variant manifests

The graphics cmod also ships [`cmods/graphics/manifest.py`](../../cmods/graphics/manifest.py) with `freeze_as_str` for a subset of pure-Python fallbacks — used when that manifest is included directly, separate from the `package("graphics", …)` line in the root manifest.

### Summary for frozen builds

| Stage | Input | Output in firmware |
|-------|-------|-------------------|
| `build_mp.sh` freeze | `.py` from cmods sub-repos + port manifests | **Embedded `.mpy` bytecode** (or `freeze_as_str` text for listed files) |
| micropython-lib MIP | `.py` in micropython-lib checkout | **Filesystem `.mpy`** (or `.py` via `--no-mpy`) |
| GitHub MIP | `.py` in pydisplay repo | **Filesystem `.py`** |

Frozen modules are importable by name but do not appear as separate files on `:lib:` or the flash filesystem unless a port also exposes them there.
