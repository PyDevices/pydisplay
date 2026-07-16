# 🤝 Contributing

pydisplay is a community project. Bug reports, board configs, drivers, docs, and examples are all welcome.

## Development setup

See **[Building and publishing documentation](building-docs.md)** for local preview (`mkdocs serve`) and ReadTheDocs setup.

Quick version:

```bash
python3 -m venv .venv-docs
.venv-docs/bin/pip install -r docs/requirements.txt
.venv-docs/bin/mkdocs serve    # http://127.0.0.1:8000
```

After editing files under `src/` (or install pre-commit hooks — see below):

```bash
./scripts/install_refresh_manifests.sh    # refresh packages/*.json and web/pyscript/micropython.toml
```

Optional — run codegen on commit (CI still audits if you skip this):

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pre-commit install
```

Hooks refresh install manifests when `src/` changes and the PyScript gallery when
`src/examples/` (or gallery scripts) change.

## Pull request workflow

1. Fork [PyDevices/pydisplay](https://github.com/PyDevices/pydisplay)
2. Create a feature branch
3. Make changes; run `./scripts/install_refresh_manifests.sh --audit` if you touched `src/` (or use pre-commit)
4. For docs: see [Building docs](building-docs.md) — `mkdocs serve` and verify pages build
5. Open a PR against `main` with a clear description

## High-value contributions

- **Board configs** for new hardware
- **Display/touch drivers** for unsupported controllers
- **C bus drivers** (STM32, i.MX RT) compatible with BusDisplay
- **Documentation** fixes and platform guides — see [docstring conventions](contributing/docstrings.md)
- **EPaperDisplay** implementation
- **CircuitPython** board configs and circup packaging
- **PyScript** asyncio examples and psdisplay improvements

## Code style

Python is linted with Ruff — see `pyproject.toml`. With `pre-commit install`, hooks
run Ruff, strip notebook outputs, refresh install manifests, and refresh the PyScript
gallery (narrow paths). CI keeps `--audit` / `--check` gates for contributors who do
not use pre-commit.

Public API docstrings: [Docstring conventions](contributing/docstrings.md).

## Documentation

**Maintainer releases** (micropython-lib, MIP index, TestPyPI): [How to release](publishing-micropython-lib.md#how-to-release) in [Publishing micropython-lib](publishing-micropython-lib.md). CI and scripts: [`scripts/README.md`](https://github.com/PyDevices/pydisplay/blob/main/scripts/README.md).

## License

Follow the license terms in the repository. Third-party add_ons retain their original licenses where noted.
