# pydisplay `scripts/`

Repo and site maintenance scripts. Each runnable script uses a **domain prefix** (`install_`, `pyscript_`, `mkdocs_`, `publish_`, `assets_`).

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
| `publish_` | `publish_micropython_lib.sh`, `publish_mip_index.py`, `publish_make_pyproject.py` | Release to micropython-lib / mip index (infrequent) |
| `assets_` | `assets_convert_md_png_to_pbm.py` | Icon PNG → PBM conversion (rare) |

`manifestfile.py` is a shared library for the publish scripts (not prefixed).

Manual packages (not generated): `packages/i80bus.json`, `packages/spibus.json`.
