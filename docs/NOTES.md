# Personal notes

Private working notes for this repo. Not part of the published docs.

## Todo

<!-- Add items when asked to "add … to my todo list". Use `- [ ]` checkboxes. -->

- [ ] Frozen self-installer for MicroPython (Unix + `micropython.exe`) — see [notes](#frozen-self-installer-notes) below
  - [ ] Warn users where downloads come from: PyDevices micropython-lib MIP index (`https://PyDevices.github.io/micropython-lib/mip/PyDevices`), not the [official MicroPython micropython-lib](https://github.com/micropython/micropython-lib) package index — **maintainer-published**, not an endorsed upstream source (show URL on first run / in GUI)
  - [ ] Freeze a small bootstrap module into desktop MicroPython builds so `from <xyz> import <clever_install_fn>` works out of the box
  - [ ] Install or refresh all 4 core modules (`displaysys`, `eventsys`, `graphics`, `multimer`) via `mip` / `lib_install`-style fetch (skip re-download when up to date?)
  - [ ] Post-install GUI (TBD: terminal menu vs minimal on-display UI): download more files, system/platform info, `lv_test_timer_*`-style sanity checks, link to `spotapi_remote` / spotapi
  - [ ] Flesh out scope, module name, and UX (name the import, entry points, error handling offline)

- [ ] Develop apps and freeze them into standalone executables — start with `spotapi_remote` in the spotapi repo

### Frozen self-installer notes

Private design scratchpad (not for RTD).

**Goal:** One-liner onboarding on MicroPython Unix and `micropython.exe` without requiring users to copy `installer.py` manually first.

**Bootstrap API (draft):**

```python
from <xyz> import <clever_install_fn>  # name TBD
<clever_install_fn>()  # fetch or refresh core libs, then optional GUI
```

**What gets installed first:** The four `src/lib` packages only — same set as micropython-lib `pydisplay-bundle` core (`displaysys`, `eventsys`, `graphics`, `multimer`). Add-ons, examples, and board configs stay optional later steps.

**Source of truth:** Maintainer-published packages from the PyDevices micropython-lib fork, published via `scripts/publish_micropython_lib.sh` → MIP index at `https://PyDevices.github.io/micropython-lib/mip/PyDevices`. Same channel as `installer.py` `lib_install()` ([`docs/installation/mip-micropython-lib.md`](docs/installation/mip-micropython-lib.md) on RTD describes the index; this installer should **warn explicitly** that it is not the official MicroPython micropython-lib registry).

**Suggested first-run warning (UI copy):**

> Installing from PyDevices micropython-lib (maintainer-published community index).  
> Not the official MicroPython package registry.  
> Index: `https://PyDevices.github.io/micropython-lib/mip/PyDevices`

**Post-install GUI ideas (pick subset for v1):**

| Area | Ideas |
|------|--------|
| More packages | `add_ons`, `examples`, `board_config.py`, `path.py`, board_configs, display/touch drivers |
| System info | Platform, `sys.implementation`, free memory, display backend detected, timer backend (`Timer` vs `AsyncTimer`) |
| Diagnostics | Run or launch patterns like `lv_test_timer_no_pump` / `lv_test_timer_pump` / `lv_test_timer_async` / harness — platform labels, timer tick, optional touch |
| Integrations | Deep link or install hook for `spotapi_remote` / spotapi (`src/examples/spotapi` is local-only symlink today) |
| Maintenance | Refresh core libs, show installed versions, clear and reinstall |

**Existing code to reuse / align with:**

- [`installer.py`](installer.py) — `lib_install()` vs `repo_install()` split
- [`scripts/publish_micropython_lib.sh`](scripts/publish_micropython_lib.sh) — what actually lands on the MIP index
- Desktop `board_config` in `src/lib/board_config.py` — likely still needed after core install

**Open questions:**

- Frozen module lives in pydisplay repo vs MicroPython port tree?
- Idempotent refresh: version manifest, etag, or always pull?
- GUI toolkit on desktop MCU port: `pdwidgets`, plain print menu, or SDL text UI?
- Relationship to future TestPyPI / pip path for CPython Jupyter (separate track)

- [ ] Find all globals in `src/lib`
- [ ] Trim `jupyter_notebook.ipynb` out of `pyscript.toml` (demo pages don't need it; bundled via `gen_repo_packages.py`)
- [ ] Jupyter install notebook: add `board_config.py` to the `displaysys` TestPyPI package (may need default `board_config` to work without eventsys)
- [ ] Ensure each `src/lib` package is installable alone — no hard dependency on the other pydisplay libs being installed
- [ ] Make sure all desktop backends exit gracefully in `displaysys`
- [x] Compile MicroPython with `os.dupterm` enabled
