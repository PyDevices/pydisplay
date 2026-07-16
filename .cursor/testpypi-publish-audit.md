# TestPyPI and release automation audit

Inventory of PyDevices repos that publish to **TestPyPI** or **micropython-lib / MIP**, what each workflow builds, and gaps vs the goals in `docs/NOTES.md` (GitHub release assets per tag; linux + windows + Android wheels where applicable).

Audited **2026-07-08** from local clones under `~/github/cmods` and `~/github/pydisplay`, plus live TestPyPI JSON and `gh` API.

## Summary

| Repo | Workflow | Trigger | TestPyPI | MIP / micropython-lib | GH release assets |
|------|----------|---------|----------|----------------------|-------------------|
| **pydisplay** | [`publish-micropython-lib.yml`](../.github/workflows/publish-micropython-lib.yml) | tag `v*.*.*` | yes (pure-Python wheels) | yes (sync + gh-pages MIP) | **no** |
| **usdl2** | `publish-testpypi.yml` | tag `v*.*.*` | yes (`py3-none-any`) | no | **no** (tags only) |
| **graphics** | `publish-testpypi.yml` | tag `v*.*.*` | yes (cibuildwheel) | frozen via `cmods/manifest.py` | **no** (tags only) |
| **lv_cpython_mod** | `publish-testpypi.yml` + `sync-and-release.yml` | tag / dispatch | yes (cibuildwheel) | no (CPython binding) | **no** (tags only) |
| **lv_bindings** | `trigger-lv-cpython-mod-release.yml` | push to `generated/` | indirect | no | **no** |

**No PyDevices publish workflow currently creates a GitHub Release or attaches build artifacts.** Tag pushes upload to TestPyPI (and pydisplay also updates micropython-lib + MIP gh-pages).

## pydisplay → micropython-lib + TestPyPI

**Script:** [`scripts/publish_micropython_lib.sh`](../scripts/publish_micropython_lib.sh)  
**CI:** runs on `ubuntu-latest` only; `hatch build` + `twine upload` per package.

**TestPyPI packages today** (from manifest `pypi_publish=` names):

| Package | Example wheel (v0.0.7) | Platform model |
|---------|------------------------|----------------|
| `displaysys` | `displaysys-0.0.7-py2.py3-none-any.whl` | universal; core + `board_config.py` (next publish) |
| `eventsys` | `eventsys-0.0.7-py2.py3-none-any.whl` | universal |
| `multimer` | `multimer-0.0.7-py2.py3-none-any.whl` | universal |
| `pydisplay-graphics` | `pydisplay_graphics-0.0.7-py2.py3-none-any.whl` | universal (PyPI name mapped from `graphics`) |

**Layout:** `displaysys` is the full package (all modules under `src/lib/displaysys/` plus `board_config.py`). Optional `displaysys-*` backend wheels remain for small MIP installs only — do not stack them on top of the full `displaysys` wheel on CPython. Published packages do not include `examples/` trees.

**Not on TestPyPI yet (until next pydisplay tag release):** ~~`displaysys-*` backend subpackages~~ — published from v0.0.8+; see [naming convention](testpypi-naming-convention.md).

**Linux / Windows / Android:** universal `none-any` wheels install on all three; no per-OS wheel matrix is required for these packages.

**micropython-lib / MIP:** same workflow runs [`scripts/publish_mip_ghpages.sh`](../scripts/publish_mip_ghpages.sh) — compiles `.mpy` index to the `gh-pages` branch (`mip/PyDevices/…`). That index is **not** attached to GitHub Releases either.

**Secrets:** `MICROPYTHON_LIB_DEPLOY_TOKEN`, `TESTPYPI_API_TOKEN`.

## Native extension repos (cibuildwheel)

Both use the same shape: matrix `ubuntu-latest` + `windows-latest`, plus a dedicated Android job (`CIBW_PLATFORM=android`), then merge artifacts and `twine upload`.

### graphics (`graphics-cmod`)

- **Workflow:** `graphics/.github/workflows/publish-testpypi.yml`
- **TestPyPI:** verified `0.0.1` — 14 wheels: `manylinux` + `win_amd64` for cp310–cp314, `android_21_arm64_v8a` + `android_21_x86_64` for cp313–cp314
- **Config:** `graphics/pyproject.toml` `[tool.cibuildwheel]`

### lv_cpython_mod (`lvgl-cpython`)

- **Workflows:** `publish-testpypi.yml`; `sync-and-release.yml` (dispatch from lv_bindings or manual)
- **Chain:** `lv_bindings` push to `generated/lvgl_python.c` → `trigger-lv-cpython-mod-release.yml` → sync + auto tag + publish
- **TestPyPI:** verified `9.5.6` — same 14-wheel pattern as graphics
- **Secrets:** `TESTPYPI_API_TOKEN`, `RELEASE_WORKFLOW_TOKEN` (tag push must use PAT so publish workflow fires)

## usdl2

- **Workflow:** `usdl2/.github/workflows/publish-testpypi.yml`
- **Package:** pure-Python ctypes shim (`py3-none-any`); native code is the **MicroPython user C module** built into firmware, not a CPython wheel
- **Linux / Windows / Android:** one universal wheel is intentional — Android/desktop load `libSDL2.so` / `SDL2.dll` at runtime via ctypes
- **Tags on GitHub:** semver release tags (`v*.*.*`) exist; **no GitHub Release** objects

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

## Gap analysis vs NOTES todos

### “Wheels for unix, windows, and Android”

| Category | Status |
|----------|--------|
| **Native CPython extensions** (`lvgl-cpython`, `graphics-cmod`) | **Met** — CI builds linux + windows + android wheels |
| **Pure pydisplay libs** (`displaysys`, `eventsys`, `multimer`, `pydisplay-graphics`) | **Met by design** — universal wheels; manifest `require()` graph in § Pip dependency graph |
| **usdl2** | **Met for CPython shim** — universal wheel; MP cmod is separate |
| **displayif** | **N/A** — firmware-only user C module, not a pip/MIP package |
| **displaysys-* backends** | **Published** (v0.0.8+) — see [naming convention](testpypi-naming-convention.md) |

No change needed for cibuildwheel repos unless you want **more Android ABIs** or **older CPython minors on Android** (today android wheels are cp313–cp314 only, per `pyproject.toml` comments).

### Pip dependency graph (`publish_micropython_lib.sh` manifests)

Declared for the next tag publish (MIP + TestPyPI `pyproject.toml`):

| Package | `require()` / PyPI deps |
|---------|-------------------------|
| `eventsys` | `multimer` |
| `multimer` | *(none — stdlib backends on CPython; `usdl2` only if sdl2 timer backend is selected at runtime)* |
| `displaysys-pgdisplay` | `displaysys`, `eventsys` (`pygame-ce` install separately) |
| `displaysys-sdldisplay` | `displaysys`, `eventsys` (`usdl2` install separately) |
| `displaysys-psdisplay`, `displaysys-jndisplay` | `displaysys`, `eventsys` |
| Other `displaysys-*` | `displaysys` only |

Install any of these from TestPyPI using the [two-index `pip` command](../docs/publishing-micropython-lib.md#two-index-pip-install-required): TestPyPI as `-i` (PyDevices packages) and PyPI as `--extra-index-url` (deps like `pygame-ce` that are not on TestPyPI).

After a pydisplay tag publish, run the desktop stack smoke test (headless in CI or SSH):

```bash
./tools/test_testpypi_desktop.sh --headless
```

### “GitHub release assets per tag”

**Universal gap:** every publisher uploads to TestPyPI only. Release tags exist on each repo but:

- `gh release list` shows **no releases** (or empty asset lists) for usdl2, graphics, lv_cpython_mod, and typical pydisplay tags

**Suggested implementation pattern** (not done yet):

1. After `twine upload`, add a job that runs `gh release create` (or `softprops/action-gh-release`) with `dist/*.whl` (and optionally MIP index zip / `latest.json` bundle for pydisplay).
2. For **lv_cpython_mod**, reuse downloaded cibuildwheel artifacts before upload (or re-download from TestPyPI — worse).
3. For **pydisplay MIP**, attach a tarball of `mip/PyDevices/` or link to gh-pages commit in release notes.
4. Use `contents: write` + `GITHUB_TOKEN` or a release PAT; keep `RELEASE_WORKFLOW_TOKEN` pattern where tag-created-by-bot must trigger downstream workflows.

## Related docs

- [TestPyPI naming convention](testpypi-naming-convention.md)
- [Publishing micropython-lib](../docs/publishing-micropython-lib.md)
- [scripts/README.md](../scripts/README.md)
- [mip-and-freeze-sources.md](mip-and-freeze-sources.md)
- [Android platform notes](../docs/platforms/android.md) — TestPyPI wheels for `lvgl-cpython`
