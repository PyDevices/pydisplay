# TestPyPI and release automation audit

Inventory of PyDevices repos that publish to **TestPyPI** or **micropython-lib / MIP**,
and what each workflow builds (linux / windows / Android wheels where applicable).

Audited **2026-07-08** from local clones under `~/github/cmods` and `~/github/pydisplay`, plus live TestPyPI JSON and `gh` API.

## Summary

| Repo | Workflow | Trigger | TestPyPI | MIP / micropython-lib |
|------|----------|---------|----------|----------------------|
| **pydisplay** | [`publish-micropython-lib.yml`](../.github/workflows/publish-micropython-lib.yml) | tag `v*.*.*` | yes (pure-Python wheels) | yes (sync + gh-pages MIP) |
| **usdl2** | `publish-testpypi.yml` | tag `v*.*.*` | yes (`py3-none-any`) | no |
| **graphics** | `publish-testpypi.yml` | tag `v*.*.*` | yes (cibuildwheel) | frozen via `cmods/manifest.py` |
| **lv_cpython_mod** | `publish-testpypi.yml` + `sync-and-release.yml` | tag / dispatch | yes (cibuildwheel) | no (CPython binding) |
| **lv_bindings** | `trigger-lv-cpython-mod-release.yml` | push to `generated/` | indirect | no |

Tag pushes upload to TestPyPI (and pydisplay also updates micropython-lib + MIP gh-pages).

## pydisplay → micropython-lib + TestPyPI

**Script:** [`scripts/publish_sync_packages.sh`](../scripts/publish_sync_packages.sh)  
**CI:** runs on `ubuntu-latest` only; `hatch build` + `twine upload` per package.

**TestPyPI packages today** (from manifest `pypi_publish=` names):

| Package | Example wheel (v0.0.7) | Platform model |
|---------|------------------------|----------------|
| `displaysys` | `displaysys-0.0.7-py2.py3-none-any.whl` | universal; full tree + `board_config.py` |
| `eventsys` | `eventsys-0.0.7-py2.py3-none-any.whl` | universal |
| `multimer` | `multimer-0.0.7-py2.py3-none-any.whl` | universal |
| `pygraphics` | `pydisplay_graphics-0.0.7-py2.py3-none-any.whl` | universal (PyPI name mapped from `pygraphics`) |

**Layout:** `displaysys` is the full package (all modules under `src/lib/displaysys/` plus `board_config.py`). Per-backend `displaysys-*` packages are **not** published. Published packages do not include `examples/` trees.

**Linux / Windows / Android:** universal `none-any` wheels install on all three; no per-OS wheel matrix is required for these packages.

**micropython-lib / MIP:** same workflow runs [`scripts/publish_mip_ghpages.sh`](../scripts/publish_mip_ghpages.sh) — compiles `.mpy` index to the `gh-pages` branch (`mip/PyDevices/…`).

**Secrets:** `MICROPYTHON_LIB_DEPLOY_TOKEN`, `TESTPYPI_API_TOKEN`.
## Native extension repos (cibuildwheel)

Both use the same shape: matrix `ubuntu-latest` + `windows-latest`, plus a dedicated Android job (`CIBW_PLATFORM=android`), then merge artifacts and `twine upload`.

### graphics (`pygraphics-cmod`)

- **Workflow:** `graphics/.github/workflows/publish-testpypi.yml`
- **TestPyPI:** verified `0.0.1` — 14 wheels: `manylinux` + `win_amd64` for cp310–cp314, `android_21_arm64_v8a` + `android_21_x86_64` for cp313–cp314
- **Config:** `graphics/pyproject.toml` `[tool.cibuildwheel]`

### lv_cpython_mod (`lvgl-cpython`)

- **Workflows:** `publish-testpypi.yml`; `sync-and-release.yml` (dispatch from lv_bindings or manual)
- **Chain:** `lv_bindings` push to `generated/lvgl_python.c` → `trigger-lv-cpython-mod-release.yml` → sync + auto tag + publish
- **TestPyPI:** verified `9.5.6` — same 14-wheel pattern as graphics
- **Secrets:** `TESTPYPI_API_TOKEN`, `RELEASE_WORKFLOW_TOKEN` (tag push must use PAT so publish workflow fires)

## usdl2

- **Workflows:** `usdl2/.github/workflows/publish-testpypi.yml` (native cibuildwheel);
  `publish-micropython-lib.yml` (TestPyPI `usdl2-py` + MIP)
- **Native package:** platform wheels (`manylinux`, `win_amd64`, `android_21_*`) —
  CPython extension + MicroPython/CircuitPython usermod
- **Pure Python:** `usdl2-py` / MIP `usdl2` from `lib/usdl2.py` (ctypes/ffi fallback);
  same `vX.Y.Z` as native

## Repos without TestPyPI automation

| Repo | Role | Gap |
|------|------|-----|
| **displayif** | MCU display driver user C module | firmware-only (`USER_C_MODULES`); never micropython-lib / TestPyPI |
| **lv_micropython_cmod** | LVGL MP glue | frozen in firmware / USER_C_MODULES |
| **lv_circuitpython_cmod** | LVGL CP glue | separate build path |
| **pydisplay_android** | p4a recipes + APK | consumes TestPyPI wheels; does not publish |
| **pydisplay_cmods** | board cmod helpers | no publish workflow |
| **spotapi** | unrelated client lib | no TestPyPI workflow in tree |
| **micropython-lib** (fork) | MIP host | CI builds index on push when org var set; pydisplay release owns PyDevices MIP publish |

## Gap analysis

### Wheels for unix, windows, and Android

| Category | Status |
|----------|--------|
| **Native CPython extensions** (`lvgl-cpython`, `pygraphics-cmod`) | **Met** — CI builds linux + windows + android wheels |
| **Pure pydisplay libs** (`displaysys`, `eventsys`, `multimer`, `pygraphics`) | **Met by design** — universal wheels; manifest `require()` graph in § Pip dependency graph |
| **usdl2** | **Met for CPython shim** — universal wheel; MP cmod is separate |
| **displayif** | **N/A** — firmware-only user C module, not a pip/MIP package |
| **displaysys-* backends** | **Removed** — use full `displaysys` only |

No change needed for cibuildwheel repos unless you want **more Android ABIs** or **older CPython minors on Android** (today android wheels are cp313–cp314 only, per `pyproject.toml` comments).

### Pip dependency graph (`publish_sync_packages.sh` manifests)

Declared for the next tag publish (MIP + TestPyPI `pyproject.toml`):

| Package | `require()` / PyPI deps |
|---------|-------------------------|
| `displaysys` | `eventsys` |
| `eventsys` | `multimer` |
| `multimer` | *(none — stdlib backends on CPython; `usdl2` only if sdl2 timer backend is selected at runtime)* |

MIP package.json emits these as `"deps"` (required package files are not bundled). Desktop backends still need `usdl2` / `pygame-ce` installed separately.

Install from TestPyPI using the [two-index `pip` command](../docs/publishing-micropython-lib.md#two-index-pip-install-required): TestPyPI as `-i` (PyDevices packages) and PyPI as `--extra-index-url` (deps like `pygame-ce` that are not on TestPyPI).

After a pydisplay tag publish, run the desktop stack smoke test (headless in CI or SSH):

```bash
./tools/test_testpypi_desktop.sh --headless
```

## Related docs

- [TestPyPI naming convention](testpypi-naming-convention.md)
- [Publishing micropython-lib](../docs/publishing-micropython-lib.md)
- [scripts/README.md](../scripts/README.md)
- [mip-and-freeze-sources.md](mip-and-freeze-sources.md)
- [Android platform notes](../docs/platforms/android.md) — TestPyPI wheels for `lvgl-cpython`
