# pydisplay `scripts/`

Repo and site maintenance scripts. Each runnable script uses a **domain prefix** (`install_`, `pyscript_`, `mkdocs_`, `publish_`, `assets_`).

## GitHub Actions

### Overview

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| [`manifests.yml`](../.github/workflows/manifests.yml) | Automatic (path-filtered) + manual | Manifest freshness checks |
| [`tests.yml`](../.github/workflows/tests.yml) | Automatic (path-filtered) + manual | Unit tests (`tests/`) |
| [`docs.yml`](../.github/workflows/docs.yml) | Automatic (path-filtered) + manual | `mkdocs build` (verify only; no deploy) |
| [`deploy-pyscript.yml`](../.github/workflows/deploy-pyscript.yml) | Automatic (path-filtered) + manual | Manifest checks, then deploy browser demo to `gh-pages` |
| [`publish-micropython-lib.yml`](../.github/workflows/publish-micropython-lib.yml) | **Tag push `v*.*.*`** + manual | Sync micropython-lib, MIP index, TestPyPI (full publish on tag) |

**Automatic** workflows run on **push to `main`** and on **pull requests** when matching paths change. The first four also support **Run workflow** (`workflow_dispatch`).

**Release publish:** push a semver tag (`v0.0.5`) — see [`publish_release_tag.sh`](publish_release_tag.sh). Manual dispatch remains for retries without a new tag.

### Automatic workflows

**Manifest freshness** — runs when `src/`, `packages/`, `web/pyscript/`, `sim/wokwi/`, `scripts/install_*`, or `scripts/pyscript_gen_packages.py` change:

- `install_refresh_manifests.sh --audit`
- `pyscript_gen_packages.py --check`

**Unit tests** — runs when `src/lib/` or `tests/` change:

- `python -m unittest discover -s tests`

**Documentation** — runs when `docs/`, `mkdocs.yml`, `scripts/mkdocs_gen_ref_pages.py`, `src/lib/`, or `src/add_ons/` change:

- `mkdocs build` (ReadTheDocs hosts [pydisplay.readthedocs.io](https://pydisplay.readthedocs.io) separately)

**Deploy PyScript site** — runs when `web/`, `src/`, or `scripts/pyscript_gen_packages.py` change:

1. Same manifest audits as **Manifest freshness**
2. Assemble `_site/` (PyScript app, `src/lib`, add-ons, examples, landing page)
3. Push to [`gh-pages`](https://PyDevices.github.io/pydisplay/) via `peaceiris/actions-gh-pages` (uses `GITHUB_TOKEN`; no extra secret)

### How to release

Full checklist: [Publishing micropython-lib → How to release](../docs/publishing-micropython-lib.md#how-to-release).

```bash
git checkout main && git pull
./scripts/publish_release_tag.sh X.Y.Z --push
```

That pushes tag `vX.Y.Z` and triggers sync + TestPyPI + MIP index. See [Publish secrets](#publish-secrets) below.

### Release publish (`publish-micropython-lib.yml`)

**Tag push** (`vX.Y.Z`) — full publish (sync + TestPyPI + MIP):

```bash
./scripts/publish_release_tag.sh 0.0.5 --push
```

Version comes from the git tag (no `VERSION` file). [`publish_micropython_lib.sh`](publish_micropython_lib.sh) also accepts `--version` or `PYDISPLAY_VERSION` for local runs.

**Manual dispatch** (Actions → Publish micropython-lib) — optional inputs:

| Input | Default | Meaning |
|-------|---------|---------|
| Version | — | Semver `X.Y.Z` (required unless ref is a tag) |
| Sync sources | on | Copy `src/` into micropython-lib |
| Upload TestPyPI wheels | off | TestPyPI upload |
| Rebuild MIP index | on | Rebuild `mip/PyDevices` |
| Commit message | (auto) | micropython-lib commit text |

Full walkthrough: [Publishing micropython-lib](../docs/publishing-micropython-lib.md).

### Publish secrets

| Secret | Required | Purpose |
|--------|----------|---------|
| `MICROPYTHON_LIB_DEPLOY_TOKEN` | yes | PAT with `contents:write` on [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib) |
| `TESTPYPI_API_TOKEN` | yes for tag releases | TestPyPI upload when a `vX.Y.Z` tag is pushed |

### What runs on push to `main`?

Depends on changed paths — unrelated edits skip workflows:

| You changed… | Typical workflows |
|--------------|-------------------|
| `src/lib/` | Manifest freshness, Unit tests, Deploy PyScript (+ Documentation if add-ons also changed) |
| `docs/` only | Documentation |
| `scripts/publish_*` | nothing on push to `main` |
| Push tag `vX.Y.Z` | **Publish micropython-lib** (sync + TestPyPI + MIP) |
| README / assets only | nothing (no workflow watches those paths) |

## Quick start

```bash
# After adding/removing files under src/lib, src/add_ons, or src/examples:
./scripts/install_refresh_manifests.sh --audit   # preview drift
./scripts/install_refresh_manifests.sh             # apply

# After changing example PyScript headers or gallery card copy:
python scripts/pyscript_gen_packages.py
python scripts/pyscript_gen_packages.py --check    # CI freshness
```

## By prefix

| Prefix | Scripts | When to run |
|--------|---------|-------------|
| `install_` | `install_gen_manifests.py`, `install_refresh_manifests.sh` | `src/` tree changes → updates `packages/*.json`, `web/pyscript/pyscript.toml`, `sim/wokwi/pydisplay-bundle.json` |
| `pyscript_` | `pyscript_gen_packages.py` | Gallery cards + `web/pyscript/*.json` manifests |
| `mkdocs_` | `mkdocs_gen_ref_pages.py`, `mkdocs_gen_notebook_pages.py` | Automatically on `mkdocs build` |
| `publish_` | `publish_micropython_lib.sh`, `publish_release_tag.sh`, `build.py`, `publish_mip_ghpages.sh`, `publish_make_pyproject.py` | Tag push → CI release; or local / manual workflow |
| `assets_` | `assets_convert_md_png_to_pbm.py` | Material Design PNG → PBM under `assets/icons/` (rare) |

`manifestfile.py` is a shared library for the publish scripts (not prefixed).

Manual packages (not generated): `packages/i80bus.json`, `packages/spibus.json`, `packages/i2cbus.json`, `packages/epaper_chip.json`, `packages/boarddisplay.json`, `packages/pixeldisplay.json`, `packages/epaperdisplay.json`, `packages/rgbframebuffer.json`, `packages/tt21100.json`, `packages/stmpe610.json`, `packages/keypad_shift.json`.

Personal-only example symlinks under `src/examples/` (`frogger`, `spotapi`, `spotify_remote`, …) are listed in [`personal_examples.py`](personal_examples.py) and excluded from `install_gen_manifests`, `pyscript_gen_packages`, and CI.
