# Building and publishing documentation

How to preview docs on your machine and publish them to [ReadTheDocs](https://pydisplay.readthedocs.io).

## Preview locally

From the repository root:

```bash
python3 -m venv .venv-docs
.venv-docs/bin/pip install -r docs/requirements.txt
.venv-docs/bin/mkdocs serve
```

Open **http://127.0.0.1:8000** in your browser. MkDocs reloads when you edit files under `docs/`.

One-shot production build (output in `site/`):

```bash
.venv-docs/bin/mkdocs build
```

!!! tip "Already have the venv?"
    If `.venv-docs/` exists from a previous session, skip the `venv` and `pip install` lines and run `.venv-docs/bin/mkdocs serve` directly.

### What runs during a build

| File | Role |
|------|------|
| [`mkdocs.yml`](https://github.com/PyDevices/pydisplay/blob/main/mkdocs.yml) | Site config, theme, navigation |
| [`docs/requirements.txt`](https://github.com/PyDevices/pydisplay/blob/main/docs/requirements.txt) | Python packages for MkDocs and plugins |
| [`.readthedocs.yaml`](https://github.com/PyDevices/pydisplay/blob/main/.readthedocs.yaml) | ReadTheDocs build settings (same deps) |
| [`tools/gen_ref_pages.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/gen_ref_pages.py) | Auto-generates API reference stubs from `src/lib/` |

API reference pages under `reference/` are generated at build time — do not hand-edit them.

### Troubleshooting

**`ModuleNotFoundError` during build** — use a venv as shown above; do not `pip install` into the system Python on Debian/Ubuntu (externally-managed-environment error).

**Griffe warnings** — docstring parameter mismatches in source; warnings only, build still succeeds.

**MkDocs 2.0 warning banner** — harmless; set `DISABLE_MKDOCS_2_WARNING=true` to hide it.

#### ReadTheDocs: "Builds disabled due to consecutive failures"

This project was registered on ReadTheDocs before the docs revamp. RTD kept building **`main`**, which had broken MkDocs config (missing nav pages, no `docs/requirements.txt`, wrong mkdocstrings paths). After 25 failures, RTD auto-disabled builds.

**Fix:**

1. **Admin** → **Settings** → Advanced → uncheck **Disable builds for this project** → Save.
2. **Push fixes to `main`** — RTD builds from the default branch; it cannot build changes that exist only locally.
3. **Admin** → **Versions** → ensure **`latest`** is active → click **Build version**.
4. Confirm the build log shows MkDocs Material and `docs/requirements.txt` installing — not the old readthedocs theme with missing `test2.md`.

#### ReadTheDocs: "Search indexing has been disabled"

Harmless for now — RTD pauses search indexing on inactive projects. After docs are live and receiving traffic:

**Admin** → **Settings** → **Enable search indexing** → Save.

---

## Publish to ReadTheDocs

The public docs URL is **https://pydisplay.readthedocs.io**. ReadTheDocs reads [`.readthedocs.yaml`](https://github.com/PyDevices/pydisplay/blob/main/.readthedocs.yaml) from the repo and runs the same MkDocs build as locally.

### First-time setup

1. Go to [readthedocs.org](https://readthedocs.org) and sign in with **GitHub** (same account that owns `PyDevices/pydisplay`).

2. Open the [Read the Docs dashboard](https://app.readthedocs.org/dashboard/) and click **Add project**.

3. Search for **`PyDevices/pydisplay`** and import it.
   - If the repo does not appear, install the [Read the Docs GitHub App](https://github.com/apps/readthedocs) on the `PyDevices` org or your fork, then retry.

4. On the setup form, confirm:
   - **Documentation type:** MkDocs (auto-detected from `.readthedocs.yaml`)
   - **Configuration file:** `.readthedocs.yaml`
   - Click **Next**, then **This file exists** (the config is already in the repo).

5. **Build `latest` (tracks `main`):**
   - Go to **Admin** → **Versions**.
   - Ensure **`latest`** is **Active** and set as the **default version**.
   - Click **Build** on `latest` (or wait for the webhook after pushing to `main`).

6. Check the **Builds** tab. A successful build ends with `Documentation built successfully`. The site appears at:
   - `https://pydisplay.readthedocs.io/en/latest/`
   - `https://pydisplay.readthedocs.io/` when `latest` is the default

### Ongoing

1. RTD rebuilds automatically when you push to `main`.
2. Optionally disable old version slugs (e.g. `docs-revamp`) under **Admin** → **Versions**.
3. Enable **search indexing** under **Settings** once the site is live.

### Optional: pull request previews

In RTD project **Admin** → **Preview documentation from pull requests**, enable PR builds so each PR gets a preview URL before merge.

---

## Remaining rollout checklist

Use this after ReadTheDocs is connected:

| Step | Action | Status |
|------|--------|--------|
| **Push to main** | Merge docs revamp and `git push origin main` | Done |
| **RTD build** | Re-enable builds; trigger **Build** on `latest` in RTD Admin → Versions | ☐ |
| **Verify live URLs** | Docs: `https://pydisplay.readthedocs.io` · Demo: `https://PyDevices.github.io/pydisplay/demo/` · Landing: `https://PyDevices.github.io/pydisplay/` | ☐ |

### Push to main

```bash
git checkout main
git merge docs-revamp
git push origin main
```

This runs [`.github/workflows/deploy-demo.yml`](https://github.com/PyDevices/pydisplay/blob/main/.github/workflows/deploy-demo.yml), which deploys the PyScript demo to GitHub Pages at `/demo/`.

| URL | Expected content |
|-----|------------------|
| `pydisplay.readthedocs.io` | Full MkDocs site (Material theme, all nav sections) |
| `PyDevices.github.io/pydisplay/` | Short landing page with links to docs and demo |
| `PyDevices.github.io/pydisplay/demo/` | PyScript calculator / REPL / test pages |

---

## Maintainer reference

More on regenerating packages and micropython-lib publishing: [tools/README.md](https://github.com/PyDevices/pydisplay/blob/main/tools/README.md#documentation-site).
