# Display ecosystem — continuation handoff (July 2026)

Handoff for picking up pydisplay display-ecosystem work in **desktop Cursor** after a pause. Summarizes what shipped, what is blocked on native cmods, and sensible next steps.

**Last release:** `v0.0.7` — micropython-lib publish **succeeded** (2026-07-06).  
**MIP index:** https://PyDevices.github.io/micropython-lib/mip/PyDevices

---

## What landed (PR #46 + publish fixes)

### displaysys backends (`src/lib/displaysys/`)

| Module | Role |
|--------|------|
| `busdisplay.py` | SPI / I80 / I2C chip drivers via bus layer |
| `fbdisplay.py` | External framebuffer (`refresh()` + memoryview) |
| `epaperdisplay.py` | E-paper: 1/2/4 bpp buffers, CP displayio push, MP `bus.send`, tri-color dual-RAM |
| `displaysys/pixeldisplay.py` | `PixelFramebuffer` + `PixelDisplay` for addressable LED grids |
| `boarddisplay.py` | Optional CP `board.DISPLAY` adapter — **not** used in board configs (explicit wiring preferred) |

Parallel RGB scanout uses **`fbdisplay.FBDisplay`** + displayif **`rgbframebuffer`** (not a separate `RGBDisplay` backend).

### Drivers (`drivers/`)

- **25+ vendored displayio chip drivers** (OLED, TFT, e-paper) + `community/st7565.py`
- **MP shims:** `epaperdisplay_chip.py`, `digitalio.py`, extended `spibus` reset
- **Touch MP:** `tt21100.py`, `stmpe610.py` (+ calibration)
- **Touch CP shims:** `drivers/touch/circuitpython/`
- **Input:** `keypad_gpio.py`, `keypad_shift.py` (PyBadge 74HC165)
- **Bus:** `i2cbus.py`
- **IO expander:** `xl9535.py` (T-RGB)
- **ST7701:** `st7701.py` with `run_init()` bit-bang (panel init only; pixel bus = displayif)

### Board configs (~121 directories, 58 `cp_*` siblings)

- Paired CP+MP configs for SPI/I80/I2C bus displays
- Built-in Adafruit boards: PyPortal, Titano, FunHouse, PyBadge, HalloWing M4, PiTFT FeatherWing, etc.
- **All vendored e-paper chips** have CP+MP pairs (via `scripts/board_config/manifests/epaperdisplay.toml` + `scripts/generate_board_configs.py`)
- `fbdisplay/t-rgb_480` — ST7701 + XL9535; MP uses `rgbframebuffer` + `FBDisplay`
- **Removed:** `cp_clue_builtin` (explicit wiring teaches MP users)

### Packages (`packages/`)

New MIP manifests: `i2cbus`, `epaper_chip`, `boarddisplay`, `pixeldisplay`, `epaperdisplay`, `rgbframebuffer`, `tt21100`, `stmpe610`, `keypad_shift`

### Tooling

| Script | Purpose |
|--------|---------|
| `scripts/vendor_circuitpython_drivers.py` | Refresh Adafruit drivers from GitHub |
| `scripts/generate_board_configs.py` | Manifest-driven `board_config.py` + `package.json` (SPI bus + e-paper + pixel grids) |
| `scripts/generate_epaper_board_configs.py` | Thin wrapper → `generate_board_configs.py --kind epaper` |
| `scripts/publish_micropython_lib.sh` | Sync to micropython-lib + TestPyPI |
| `scripts/publish_make_pyproject.py` | Hatch wheels from manifests |

### Docs (`docs/hardware/`)

- `display-interfaces.md` — interface matrix
- `driver-inventory.md` — vendored driver list
- `board-configs.md` — config catalog
- `touch-drivers.md` — touch contract + calibration
- `pydevices-roadmap.md` — cmod priorities

### Tests

~302 tests at PR merge; coverage for epaper, boarddisplay, fbdisplay/rgbframebuffer configs, st7701, tt21100, stmpe610, keypad_shift, i2cbus.

### Publish pipeline fixes (PRs #48, #49)

- `publish_make_pyproject.py` — nested subpackages (`multimer/_backends`)
- `publish_micropython_lib.sh` — explicit `displaysys-*` example board_config mappings; skip `displaysys-boarddisplay`

---

## Architecture decisions (do not undo without discussion)

| Topic | Decision |
|-------|----------|
| **BoardDisplay builtins** | No `cp_*_builtin` proliferation; keep `BoardDisplay` as optional CP-only helper |
| **RGB naming** | Parallel RGB uses `rgbframebuffer.RGBFrameBuffer` + `FBDisplay` — no `RGBDisplay` / `present()` path |
| **displayif location** | Native RGB/HUB75/Qualia drivers live in **`PyDevices/displayif`** repo (see its `HANDOFF.md`) |
| **board_config contract** | `display_drv`, `broker`, optional `touch_read_func` + `touch_rotation_table`, KEYPAD via `broker.create(type=eventsys.KEYPAD, ...)` |
| **E-paper tri-color** | `color_depth=2` (0=white, 1=black, 2=accent) + `highlight_color=True` on chip driver |
| **circup** | Postponed |

---

## Blocked board configs (need cmods)

These MP configs intentionally `raise NotImplementedError`:

| Config | Blocker | CP reference |
|--------|---------|--------------|
| `fbdisplay/t-rgb_480` | `rgbframebuffer` (works if displayif cmod installed) | N/A (MP-focused) |
| `fbdisplay/qualia_tl040hds20` | `rgbframebuffer` (works if cmod installed) | `cp_qualia_tl040hds20` |
| `fbdisplay/matrixportal_s3_64x64` | `rgbmatrix` | `cp_matrixportal_s3_64x64` |
| `fbdisplay/matrixportal_m4_64x32` | `rgbmatrix` | `cp_matrixportal_m4_64x32` |
| `fbdisplay/rgb_matrix_featherwing_64x32` | `rgbmatrix` | `cp_rgb_matrix_featherwing_64x32` |
| `pixeldisplay/neopixel_8x4` | `displaysys.pixeldisplay.PixelFramebuffer` | `cp_neopixel_8x4` |
| `pixeldisplay/dotstar_12x6` | `displaysys.pixeldisplay.PixelFramebuffer` | `cp_dotstar_12x6` |

**displayif handoff:** https://github.com/PyDevices/displayif/blob/main/HANDOFF.md (bootstrap this repo if missing)

---

## Priority roadmap

### P0 — displayif (separate repo)

1. `rgbframebuffer` on target SoC — unblocks `t-rgb_480`, Qualia, RK043
2. `rgbmatrix`, `mipidsi`, `picodvi` per board — see displayif `HANDOFF.md`

See `docs/hardware/pydevices-roadmap.md` and displayif `HANDOFF.md`.

### P1 — pydisplay after displayif lands

1. Remove `NotImplementedError` from blocked configs once cmods exist
2. Hardware validation on physical boards (T-RGB, Qualia, MatrixPortal, MagTag, PyPortal, …)
3. MIP package manifests for displayif bindings (if needed)

### P2 — deferred / skipped

| Item | Notes |
|------|-------|
| **circup** | Postponed |
| **Wokwi CP siblings** | Skipped for now |
| **RA8875** | framebuf API, not displayio — skipped |
| **RP2040 PIO I80** | `drivers/bus/_rp2_wip.py` — speed work |
| **MIPI DSI / picodvi** | P3 advanced |

### P3 — displayif generation pipeline (future)

Generate displayif cmod sources from pydisplay `board_configs/` + `drivers/` (user noted: ignore stale displayif repo contents; pydisplay is source of truth).

---

## Key files to read first

```
src/lib/displaysys/fbdisplay.py       # framebuffer scanout adapter
src/lib/displaysys/epaperdisplay.py   # tri-color / packed bpp
board_configs/fbdisplay/t-rgb_480/    # displayif rgbframebuffer integration
drivers/display/st7701.py             # T-RGB init sequence
drivers/io_expander/xl9535.py
scripts/publish_micropython_lib.sh    # release sync
docs/hardware/display-interfaces.md
docs/publishing-micropython-lib.md
```

---

## Releasing

```bash
./scripts/publish_release_tag.sh X.Y.Z --push
```

Triggers **Publish micropython-lib** workflow: sync `PyDevices/micropython-lib` `PyDevices` branch, rebuild MIP index, TestPyPI wheels.

**Gotchas fixed in v0.0.7 publish:**

- multimer nested `_backends` package layout
- displaysys example `board_config.py` paths in publish script

---

## Suggested next pydisplay PRs (when you return)

1. **After displayif RGB565 works:** integration test doc + un-skeleton `t-rgb_480` on hardware
2. **PIO I80:** finish RP2040 fast path for LilyGO I80 boards
3. **Manifest freshness CI** — check failing jobs on main if still red
4. **Wokwi CP siblings** — if simulation parity becomes important
5. **displayif codegen script** — sketch `scripts/generate_displayif_*.py` from board configs

---

## Branches / cleanup

| Branch | Status |
|--------|--------|
| `cursor/display-ecosystem-foundation-7b24` | Merged via PR #46 — safe to delete |
| `cursor/fix-multimer-testpypi-7b24` | Merged PR #48 — safe to delete |
| `cursor/fix-displaysys-board-config-publish-7b24` | Merged PR #49 — safe to delete |

---

## Desktop Cursor setup

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # if present
pytest tests/
```

For MCU work: clone `micropython-lib`, `cmods`, `displayif` per `docs/installation/` and displayif `HANDOFF.md`.

---

*Generated 2026-07-06 after micropython-lib v0.0.7 publish succeeded.*
