# Publishing micropython-lib and TestPyPI

How to sync pydisplay into the [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib) fork, rebuild the MIP index, and optionally upload wheels to TestPyPI.

There are **three related outputs**:

| Output | Where it lives | What users get |
|--------|----------------|----------------|
| **Source packages** | [micropython-lib](https://github.com/PyDevices/micropython-lib) branch `PyDevices` | `manifest.py` trees under `micropython/pydisplay/` |
| **MIP index** | [micropython-lib `gh-pages`](https://github.com/PyDevices/micropython-lib/tree/gh-pages) → `mip/PyDevices/` | Precompiled `.mpy` for `mip.install(..., index=...)` |
| **TestPyPI wheels** | [test.pypi.org](https://test.pypi.org) | CPython-installable wheels (dev/testing only) |

Install URL for MicroPython boards:

```text
https://PyDevices.github.io/micropython-lib/mip/PyDevices
```

User-facing install docs: [micropython-lib MIP](installation/mip-micropython-lib.md).

---

## Before you publish

1. **Merge to `main`** on [PyDevices/pydisplay](https://github.com/PyDevices/pydisplay) — publish from a commit you are happy with.

2. **Repository secrets** on pydisplay (Settings → Secrets and variables → Actions):

   | Secret | Required | Purpose |
   |--------|----------|---------|
   | `MICROPYTHON_LIB_DEPLOY_TOKEN` | yes | PAT with **Contents: read/write** on `PyDevices/micropython-lib` |
   | `TESTPYPI_API_TOKEN` | no | TestPyPI upload when “Upload TestPyPI wheels” is enabled |

3. **Optional: bump version** in [`scripts/VERSION`](https://github.com/PyDevices/pydisplay/blob/main/scripts/VERSION) (or set `PYDISPLAY_VERSION` for one-off runs). That version is written into micropython-lib `manifest.py` files and affects MIP package versions.

4. **CI green on `main`** — Manifest freshness and Unit tests should pass. Personal example symlinks (`frogger`, `spotapi`, `spotify_remote`, …) are excluded from automation via [`scripts/personal_examples.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/personal_examples.py).

---

## GitHub Actions (recommended)

Workflow: [`.github/workflows/publish-micropython-lib.yml`](https://github.com/PyDevices/pydisplay/blob/main/.github/workflows/publish-micropython-lib.yml)

### Step 1 — Open the workflow

1. [PyDevices/pydisplay → Actions](https://github.com/PyDevices/pydisplay/actions)
2. **Publish micropython-lib** (left sidebar)
3. **Run workflow** → branch **`main`**

### Step 2 — Choose inputs

| Input | Typical / first run | With TestPyPI |
|-------|-------------------|---------------|
| **Sync sources** | on | on |
| **Upload TestPyPI wheels** | **off** (faster) | **on** |
| **Publish MIP index** | on | on |
| **Commit message** | leave blank | blank or custom |

If commit message is blank, the job uses:

```text
pydisplay: Sync from PyDevices/pydisplay <sha>.
```

Micropython-lib commit messages should follow upstream style when you write your own, e.g. `pydisplay: Fix timer drift in multimer.`

### Step 3 — What the job does

**Sync sources** ([`scripts/publish_micropython_lib.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_micropython_lib.sh)):

- Copies `src/lib/*` into `micropython-lib/micropython/pydisplay/`
- Writes `manifest.py` per package (`eventsys`, `graphics`, `multimer`, `displaysys` subpackages, …)
- Commits and pushes to the **`PyDevices`** branch

**Upload TestPyPI wheels** (optional):

- For each publishable package: `publish_make_pyproject.py` → `hatch build` → `twine upload --repository testpypi`
- Uses `TESTPYPI_API_TOKEN` with `TWINE_USERNAME=__token__`

**Publish MIP index** ([`scripts/publish_mip_ghpages.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_mip_ghpages.sh)):

- Clones MicroPython and builds `mpy-cross`
- Runs [`scripts/build.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/build.py) over the micropython-lib tree
- Pushes the compiled index to **`gh-pages`** at `mip/PyDevices/`

### Step 4 — Watch the run

Typical runtime:

- Sync + MIP index: **~10–20 minutes** (mpy-cross + full index compile)
- With TestPyPI: **longer** (hatch/twine per package)

---

## Verify after publish

### micropython-lib source (`PyDevices` branch)

- [micropython/pydisplay](https://github.com/PyDevices/micropython-lib/tree/PyDevices/micropython/pydisplay) — new commit from `github-actions[bot]`

### MIP index (boards)

- Index: [PyDevices.github.io/micropython-lib/mip/PyDevices](https://PyDevices.github.io/micropython-lib/mip/PyDevices)
- Example: `…/mip/PyDevices/package/6/displaysys/latest.json` (bytecode version may differ)

On device:

```python
import mip
mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

Or `mpremote mip install --index "https://PyDevices.github.io/micropython-lib/mip/PyDevices" displaysys`

### TestPyPI

- Browse [test.pypi.org](https://test.pypi.org) for package names (`displaysys`, `eventsys`, …)
- Desktop venv test:

  ```bash
  pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ displaysys
  ```

TestPyPI is for **CPython testing**, not MicroPython on hardware.

---

## Suggested cadence

**Routine library update:**

1. Run workflow: **Sync on**, **TestPyPI off**, **MIP index on**
2. Spot-check MIP URL and one `mip.install` on hardware

**Release with desktop wheels:**

1. Bump `scripts/VERSION` if needed
2. Run with **Upload TestPyPI wheels on**
3. Confirm packages on test.pypi.org

**MIP-only refresh** (sources unchanged): Sync **off**, MIP index **on** — uncommon.

---

## Local publish (alternative)

From a pydisplay checkout:

```bash
# Sync into ~/github/micropython-lib (PyDevices branch checked out)
cd ~/github/pydisplay
./scripts/publish_micropython_lib.sh --skip-pypi
# Or non-interactive:
./scripts/publish_micropython_lib.sh \
  --skip-pypi \
  --commit-message "pydisplay: Sync from local." \
  --push

# With TestPyPI (needs hatch, twine, and TESTPYPI_API_TOKEN or ~/.pypirc)
export TESTPYPI_API_TOKEN=...
./scripts/publish_micropython_lib.sh \
  --commit-message "pydisplay: Sync and TestPyPI upload." \
  --push

# MIP index → gh-pages
MICROPYTHON_LIB_DIR=~/github/micropython-lib ./scripts/publish_mip_ghpages.sh
```

Local gh-pages push requires git credentials for micropython-lib.

Script options: `./scripts/publish_micropython_lib.sh --help`

---

## TestPyPI gotchas

| Issue | What to do |
|--------|------------|
| Version already exists | Bump `scripts/VERSION` — TestPyPI rejects duplicate versions |
| Upload fails mid-run | Partial TestPyPI uploads may succeed before the error; bump `VERSION` and re-run |
| `graphics` sdist 400 | Name is taken on [pypi.org/project/graphics](https://pypi.org/project/graphics); PyPI project is `pydisplay-graphics` (MIP name stays `graphics`) |
| Slow | Normal — each lib package gets hatch build + twine upload |
| Not for devices | Boards use the **MIP index**, not TestPyPI |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `Resource not accessible` / 403 on checkout | Missing or wrong `MICROPYTHON_LIB_DEPLOY_TOKEN` |
| Push to `PyDevices` fails | PAT lacks write access or SSO not authorized for PyDevices |
| TestPyPI 403 | Bad `TESTPYPI_API_TOKEN` |
| TestPyPI 400 on sdist (wheel OK) | PyPI project name taken on pypi.org — add a mapping in `pypi_publish_name()` in `publish_micropython_lib.sh` |
| MIP compile error | Bad `manifest.py` in micropython-lib — see job log for package path |
| `No changes to commit` | Sources already match; MIP step may still run if enabled |

---

## Related scripts

| Script | Role |
|--------|------|
| [`scripts/publish_micropython_lib.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_micropython_lib.sh) | Rsync `src/lib` → micropython-lib; optional TestPyPI |
| [`scripts/build.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/build.py) | Compile MIP index (used by `publish_mip_ghpages.sh`) |
| [`scripts/publish_mip_ghpages.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_mip_ghpages.sh) | Build index and push `mip/PyDevices` on gh-pages |
| [`scripts/publish_make_pyproject.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_make_pyproject.py) | Hatch `pyproject.toml` from firmware-style manifests |

See also [`scripts/README.md`](https://github.com/PyDevices/pydisplay/blob/main/scripts/README.md) for the full maintainer script index.
