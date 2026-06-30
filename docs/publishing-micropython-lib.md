# Publishing micropython-lib and TestPyPI

How to sync pydisplay into the [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib) fork, rebuild the MIP index, and upload wheels to TestPyPI.

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

## How to release

Use this checklist for a normal library release. Version is **only** a git tag (`vX.Y.Z`) — there is no `VERSION` file.

### 1. Prepare

- [ ] Changes are merged on [`main`](https://github.com/PyDevices/pydisplay)
- [ ] [Manifest freshness](https://github.com/PyDevices/pydisplay/actions/workflows/manifests.yml) and [Unit tests](https://github.com/PyDevices/pydisplay/actions/workflows/tests.yml) are green
- [ ] Choose a **new** semver not already on [TestPyPI](https://test.pypi.org) (TestPyPI rejects duplicate versions)
- [ ] Repository secrets are set: `MICROPYTHON_LIB_DEPLOY_TOKEN`, `TESTPYPI_API_TOKEN`

### 2. Tag and push

From a clean checkout of the commit you want to release:

```bash
git checkout main
git pull
./scripts/publish_release_tag.sh X.Y.Z --push
```

Example: `./scripts/publish_release_tag.sh 0.0.5 --push` creates annotated tag `v0.0.5` and pushes it.

Manual equivalent:

```bash
git tag -a v0.0.5 -m "Release 0.0.5"
git push origin v0.0.5
```

Tags must match `v*.*.*` (e.g. `v0.0.5`, not `0.0.5`).

### 3. CI publishes automatically

Pushing the tag starts [**Publish micropython-lib**](https://github.com/PyDevices/pydisplay/actions/workflows/publish-micropython-lib.yml), which:

1. Syncs `src/lib/*` into [micropython-lib](https://github.com/PyDevices/micropython-lib) (`PyDevices` branch) at version `X.Y.Z`
2. Uploads CPython wheels to TestPyPI (`displaysys`, `eventsys`, `pydisplay-graphics`, `multimer`, …)
3. Rebuilds the [MIP index](https://PyDevices.github.io/micropython-lib/mip/PyDevices) on micropython-lib `gh-pages`

Typical runtime: **~10–20 minutes**.

### 4. Verify

- [ ] Workflow succeeded on the [Actions tab](https://github.com/PyDevices/pydisplay/actions)
- [ ] [micropython/pydisplay](https://github.com/PyDevices/micropython-lib/tree/PyDevices/micropython/pydisplay) has a new commit from `github-actions[bot]`
- [ ] MIP index updated — e.g. `…/package/6/displaysys/latest.json` shows the new version
- [ ] TestPyPI packages exist at the new version (optional desktop check):

  ```bash
  pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ displaysys
  ```

- [ ] One hardware smoke test: `mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")`

### Retries without a new tag

**Actions → Publish micropython-lib → Run workflow** — set **Version** to `X.Y.Z`, turn **Upload TestPyPI wheels** off if that step already succeeded, and re-run sync or MIP only.

---

## Release version (git tags)

There is **no `VERSION` file**. The release version is the **git tag** on the commit you publish:

- Tag format: **`vX.Y.Z`** (e.g. `v0.0.1`, `v0.0.5`)
- That semver is written into micropython-lib `manifest.py` files and MIP package versions
- **Pushing a new tag triggers the full publish workflow** (micropython-lib sync, MIP index, TestPyPI)

Helper script:

```bash
# On the commit you want to release (usually main):
./scripts/publish_release_tag.sh 0.0.5 --push
```

Or manually:

```bash
git tag -a v0.0.5 -m "Release 0.0.5"
git push origin v0.0.5
```

---

## Before you publish

1. **Merge to `main`** on [PyDevices/pydisplay](https://github.com/PyDevices/pydisplay) — tag the commit you are happy with.

2. **Repository secrets** on pydisplay (Settings → Secrets and variables → Actions):

   | Secret | Required | Purpose |
   |--------|----------|---------|
   | `MICROPYTHON_LIB_DEPLOY_TOKEN` | yes | PAT with **Contents: read/write** on `PyDevices/micropython-lib` |
   | `TESTPYPI_API_TOKEN` | yes for tag releases | TestPyPI upload on every tag push |

3. **CI green on `main`** — Manifest freshness and Unit tests should pass. Personal example symlinks (`frogger`, `spotapi`, `spotify_remote`, …) are excluded from automation via [`scripts/personal_examples.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/personal_examples.py).

4. **TestPyPI version** — TestPyPI rejects re-uploading an existing version. Use a **new** tag (e.g. `v0.0.5` after `v0.0.4`), or delete the conflicting release on test.pypi.org first.

---

## GitHub Actions (recommended)

Workflow: [`.github/workflows/publish-micropython-lib.yml`](https://github.com/PyDevices/pydisplay/blob/main/.github/workflows/publish-micropython-lib.yml)

### Tag release (automatic)

1. Tag and push (see [Release version](#release-version-git-tags) above)
2. [Actions → Publish micropython-lib](https://github.com/PyDevices/pydisplay/actions/workflows/publish-micropython-lib.yml) runs automatically
3. Job steps:
   - **Sync sources** — copy `src/lib/*` into micropython-lib, commit/push `PyDevices` branch
   - **TestPyPI** — hatch build + twine upload for each publishable package
   - **MIP index** — compile and push `mip/PyDevices/` to micropython-lib `gh-pages`

Micropython-lib commit message (default):

```text
pydisplay: Release v0.0.5 from PyDevices/pydisplay <sha>.
```

Typical runtime: **~10–20 minutes** (MIP compile dominates; TestPyPI adds a few minutes).

### Manual dispatch (optional)

**Actions → Publish micropython-lib → Run workflow** for retries or partial publishes without a new tag:

| Input | Default | Meaning |
|-------|---------|---------|
| **Version** | — | Semver `X.Y.Z` (required unless the workflow runs on a tagged ref) |
| **Sync sources** | on | Copy `src/` into micropython-lib |
| **Upload TestPyPI wheels** | off | TestPyPI upload |
| **Publish MIP index** | on | Rebuild `mip/PyDevices` |
| **Commit message** | (auto) | micropython-lib commit text |

Tag pushes always enable sync + TestPyPI + MIP. Manual runs default to **no TestPyPI** unless you turn it on.

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

- Browse [test.pypi.org](https://test.pypi.org) for package names (`displaysys`, `eventsys`, `pydisplay-graphics`, …)
- Desktop venv test:

  ```bash
  pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ displaysys
  pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydisplay-graphics
  ```

TestPyPI is for **CPython testing**, not MicroPython on hardware.

---

## Suggested cadence

See [How to release](#how-to-release) for the full checklist. Summary:

**Library release:** merge to `main` → `./scripts/publish_release_tag.sh X.Y.Z --push` → verify workflow + MIP + optional TestPyPI.

**Retry / MIP-only (no new tag):** **Actions → Run workflow** with version set; TestPyPI off if already uploaded.

---

## Local publish (alternative)

From a pydisplay checkout on a tagged commit (or pass `--version`):

```bash
# Sync only (no TestPyPI)
git tag -a v0.0.5 -m "Release 0.0.5"   # or use publish_release_tag.sh
./scripts/publish_micropython_lib.sh --skip-pypi \
  --commit-message "pydisplay: Sync from local." --push

# With TestPyPI (needs hatch, twine, TESTPYPI_API_TOKEN or ~/.pypirc)
export TESTPYPI_API_TOKEN=...
./scripts/publish_micropython_lib.sh \
  --commit-message "pydisplay: Sync and TestPyPI upload." --push

# MIP index → gh-pages
MICROPYTHON_LIB_DIR=~/github/micropython-lib ./scripts/publish_mip_ghpages.sh
```

Local gh-pages push requires git credentials for micropython-lib.

Script options: `./scripts/publish_micropython_lib.sh --help`

---

## TestPyPI gotchas

| Issue | What to do |
|--------|------------|
| Version already exists | Push a **new tag** with a higher semver — TestPyPI rejects duplicate versions |
| Upload fails mid-run | Partial uploads may succeed; fix the error, bump the tag, push again |
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
| Workflow did not start | Tag must match `v*.*.*` (e.g. `v0.0.5`, not `0.0.5`) |

---

## Related scripts

| Script | Role |
|--------|------|
| [`scripts/publish_release_tag.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_release_tag.sh) | Create/push `vX.Y.Z` tag (triggers CI publish) |
| [`scripts/publish_micropython_lib.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_micropython_lib.sh) | Rsync `src/lib` → micropython-lib; optional TestPyPI |
| [`scripts/build.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/build.py) | Compile MIP index (used by `publish_mip_ghpages.sh`) |
| [`scripts/publish_mip_ghpages.sh`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_mip_ghpages.sh) | Build index and push `mip/PyDevices` on gh-pages |
| [`scripts/publish_make_pyproject.py`](https://github.com/PyDevices/pydisplay/blob/main/scripts/publish_make_pyproject.py) | Hatch `pyproject.toml` from firmware-style manifests |

See also [`scripts/README.md`](https://github.com/PyDevices/pydisplay/blob/main/scripts/README.md) for the full maintainer script index.
