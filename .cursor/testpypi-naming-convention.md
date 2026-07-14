# TestPyPI and pip naming convention

PyDevices publishes **CPython wheels to TestPyPI only** (not production PyPI). Each package has up to **three names**:

| Role | Example | Used by |
|------|---------|---------|
| **MIP / micropython-lib** | `graphics` | `mip.install("graphics", index=…)`, manifest `package("graphics")` |
| **pip / TestPyPI project** | `pydisplay-graphics` | `pip install … pydisplay-graphics`, hatch `[project].name` |
| **Python import** | `graphics` | `import graphics` in application code |

MIP names stay short. pip project names must **not collide with [pypi.org](https://pypi.org)** — TestPyPI rejects sdists when the normalized name is already registered there (wheels may still upload; treat collisions as errors).

---

## Rules

### 1. Default: pip name = MIP name

When [pypi.org](https://pypi.org/project/<name>/) returns **404**, use the same string for TestPyPI and MIP:

- `displaysys`, `eventsys`, `multimer`
- Optional MIP-oriented `displaysys-sdldisplay`, `displaysys-pgdisplay`, … (prefer full `displaysys` on CPython/Android)
- `usdl2` (separate repo; no collision today)

Import paths follow the wheel layout (`import displaysys`, `import displaysys.sdldisplay`, …). The full `displaysys` wheel includes every module under `src/lib/displaysys/`.

### 2. pydisplay pure-Python libs: `pydisplay-<mip-name>`

When the MIP name is **taken on pypi.org**, prefix with `pydisplay-`:

| MIP name | pip / TestPyPI | Import | Why |
|----------|----------------|--------|-----|
| `graphics` | **`pydisplay-graphics`** | `graphics` | [pypi.org/project/graphics](https://pypi.org/project/graphics) exists |

Mapping lives in `pypi_publish_name()` in [`scripts/publish_micropython_lib.sh`](../scripts/publish_micropython_lib.sh). MIP and source trees keep the short name `graphics/`.

### 3. Native CPython extensions (separate repos): suffix disambiguation

Use a **repo-specific suffix** so pip names are unique and intent is obvious:

| Pattern | pip / TestPyPI | Import | Repo |
|---------|----------------|--------|------|
| `*-cmod` | `graphics-cmod` | `graphics` | [graphics](https://github.com/PyDevices/graphics) — native FrameBuffer |
| `*-cpython` | `lvgl-cpython` | `lvgl` | [lv_cpython_mod](https://github.com/PyDevices/lv_cpython_mod) |

Do **not** publish as bare `lvgl` — [pypi.org/project/lvgl](https://pypi.org/project/lvgl) exists.

`graphics-cmod` and `pydisplay-graphics` both provide `import graphics`; prefer **`graphics-cmod`** on desktop/Android when the native wheel matches the platform, and **`pydisplay-graphics`** for pure-Python-only or cross-check installs.

### 4. displaysys backends: `displaysys-<backend>`

The main **`displaysys`** wheel is the full package (every module under `src/lib/displaysys/`) plus `board_config.py` at wheel root. Prefer that alone on CPython/Android.

Optional MIP-oriented backend wheels still use the folder name as the pip project name:

- `displaysys-sdldisplay`, `displaysys-pgdisplay`, `displaysys-busdisplay`, …
- Each ships one module under `displaysys/` and declares `require("displaysys")`.
- Do **not** install these on top of the full `displaysys` wheel on CPython (overlapping package path).
- No pypi.org collisions as of 2026-07-09.

### 5. Third-party dependencies: production PyPI only

Dependencies that live on **pypi.org** stay on the **secondary** index (`--extra-index-url`):

- `pygame-ce` (imports as `pygame`) — `displaysys-pgdisplay`
- Other upstream libs — never renamed to PyDevices prefixes

See [Two-index pip install](../docs/publishing-micropython-lib.md#two-index-pip-install-required).

### 6. Before first publish of a new name

```bash
NAME=your-package-name
curl -s -o /dev/null -w "pypi.org=%{http_code}\n" "https://pypi.org/pypi/${NAME}/json"
```

- **404** — safe to use as TestPyPI project name (same as MIP unless you choose a suffix for clarity).
- **200** — pick a mapped name; add to `pypi_publish_name()` or the native repo’s `pyproject.toml`; document in the inventory below.

After a version is on TestPyPI, **do not rename** the project (TestPyPI rejects duplicate versions; clients pin by name).

---

## Inventory (2026-07-09)

### pydisplay tag publish (`publish_micropython_lib.sh`)

| MIP / folder | pip / TestPyPI | Import | pypi.org |
|--------------|----------------|--------|----------|
| `displaysys` | `displaysys` | `displaysys`, `board_config` | free |
| `eventsys` | `eventsys` | `eventsys` | free |
| `multimer` | `multimer` | `multimer` | free |
| `graphics` | **`pydisplay-graphics`** | `graphics` | **taken** → mapped |
| `displaysys-sdldisplay` | `displaysys-sdldisplay` | `displaysys.sdldisplay` | free |
| `displaysys-pgdisplay` | `displaysys-pgdisplay` | `displaysys.pgdisplay` | free |
| `displaysys-psdisplay` | `displaysys-psdisplay` | `displaysys.psdisplay` | free |
| `displaysys-jndisplay` | `displaysys-jndisplay` | `displaysys.jndisplay` | free |
| `displaysys-busdisplay` | `displaysys-busdisplay` | `displaysys.busdisplay` | free |
| `displaysys-fbdisplay` | `displaysys-fbdisplay` | `displaysys.fbdisplay` | free |
| `displaysys-pixeldisplay` | `displaysys-pixeldisplay` | `displaysys.pixeldisplay` | free |
| `displaysys-epaperdisplay` | `displaysys-epaperdisplay` | `displaysys.epaperdisplay` | free |

### Sibling repos (own workflows)

| pip / TestPyPI | Import | pypi.org | Notes |
|----------------|--------|----------|--------|
| `graphics-cmod` | `graphics` | free | cibuildwheel; linux + windows + android |
| `lvgl-cpython` | `lvgl` | free (`lvgl` taken) | cibuildwheel; LVGL version in tag (e.g. 9.5.6) |
| `usdl2` | `usdl2` | free | pure-Python ctypes SDL2 shim |

### Firmware-only (never published)

| Module | Role | Install |
|--------|------|---------|
| **`displayif`** | User C module for MCU scanout (MIPI DSI, RGB parallel, HUB75, DVI, I80, …) | Compiled into MicroPython/CircuitPython firmware via `USER_C_MODULES` — **not** on micropython-lib, TestPyPI, or MIP |

See [PyDevices/displayif](https://github.com/PyDevices/displayif) and board configs under `board_configs/fbdisplay/`, `busdisplay/i80/`, etc.

### Deprecated / not published

| Name | Notes |
|------|--------|
| `pydisplay-bundle` | Monolithic install path — remove once per-package MIP + TestPyPI are confirmed (all `displaysys-*` backends on TestPyPI as of v0.0.8+) |

---

## Adding a new mapped name

1. Check pypi.org (and optionally test.pypi.org for PyDevices duplicates).
2. **pydisplay micropython-lib packages:** extend `pypi_publish_name()` in `publish_micropython_lib.sh`; MIP folder name unchanged.
3. **Native repos:** set `[project].name` in that repo’s `pyproject.toml`.
4. Update this inventory and [testpypi-publish-audit.md](testpypi-publish-audit.md).
5. Smoke-test: [`tools/test_testpypi_standalone.sh`](../tools/test_testpypi_standalone.sh) or [`tools/test_testpypi_desktop.sh`](../tools/test_testpypi_desktop.sh).

---

## Related docs

- [Publishing micropython-lib](../docs/publishing-micropython-lib.md)
- [TestPyPI publish audit](testpypi-publish-audit.md)
- [Installation — TestPyPI](../docs/installation/index.md#pypi--pip-testpypi)
