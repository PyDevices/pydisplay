# pydisplay `scripts/`

Repo and site maintenance scripts. Each runnable script uses a **domain prefix** (`install_`, `pyscript_`, `mkdocs_`, `publish_`, `assets_`).

## GitHub Actions

| Workflow | What it runs |
|----------|----------------|
| [`manifests.yml`](../.github/workflows/manifests.yml) | `install_refresh_manifests.sh --audit`, `pyscript_gen_packages.py --check` |
| [`tests.yml`](../.github/workflows/tests.yml) | `python -m unittest discover -s tests` |
| [`deploy-pyscript.yml`](../.github/workflows/deploy-pyscript.yml) | manifest checks, then GitHub Pages deploy |
| [`docs.yml`](../.github/workflows/docs.yml) | `mkdocs build` (runs `mkdocs_gen_*` hooks) |
| [`publish-micropython-lib.yml`](../.github/workflows/publish-micropython-lib.yml) | **manual** — sync fork, optional TestPyPI, MIP index |

### Publish secrets (`publish-micropython-lib.yml`)

| Secret | Required | Purpose |
|--------|----------|---------|
| `MICROPYTHON_LIB_DEPLOY_TOKEN` | yes | PAT with `contents:write` on [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib) |
| `TESTPYPI_API_TOKEN` | no | TestPyPI upload when workflow input “Upload TestPyPI wheels” is enabled |

Dispatch from **Actions → Publish micropython-lib → Run workflow**. Defaults: sync sources + rebuild `mip/PyDevices` (no TestPyPI).

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
| `publish_` | `publish_micropython_lib.sh`, `publish_mip_index.py`, `publish_mip_ghpages.sh`, `publish_make_pyproject.py` | Release to micropython-lib / mip index (manual workflow or local) |
| `assets_` | `assets_convert_md_png_to_pbm.py` | Material Design PNG → PBM under `assets/icons/` (rare) |

`manifestfile.py` is a shared library for the publish scripts (not prefixed).

Manual packages (not generated): `packages/i80bus.json`, `packages/spibus.json`.
