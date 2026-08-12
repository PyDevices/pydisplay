Clone the repo. From the **repository root** (not `src/`):

```bash
./bin/pyscript.sh calculator
./bin/pyscript.sh chango
./bin/pyscript.sh                    # gallery (web/pyscript/index.html)
./bin/pyscript.sh calculator --no-open
```

The script runs [`tools/serve.py`](https://github.com/PyDevices/pydevices-examples/blob/main/tools/serve.py) with Cross-Origin-Isolation headers required by PyScript, reuses a healthy server on port 8000 when one is already running, and opens the browser automatically.

| Page | Command | Purpose |
|------|---------|---------|
| Calculator | `./bin/pyscript.sh calculator` | Run one example by module name |
| Chango | `./bin/pyscript.sh chango` | Manifest demo (`packages/chango.json`) |
| Gallery | `./bin/pyscript.sh` | Example card grid |
| REPL | open `http://127.0.0.1:8000/web/pyscript/repl.html` | REPL + canvas (`terminal worker`) |
| Editor | open `http://127.0.0.1:8000/web/pyscript/editor.html` | `mpy-editor` with hidden `setup` + editable lesson |
| Async | open `http://127.0.0.1:8000/web/pyscript/async.html` | Non-blocking animation with `await` |
| DOM | open `http://127.0.0.1:8000/web/pyscript/dom.html` | HTML button → Python `create_proxy` |
| Pyodide | open `http://127.0.0.1:8000/web/pyscript/pyodide.html?modules=calc_graphics,calc_engine` or `…/pyodide.html?manifests=chango` | Modules / same MIP manifests as `micropython.html`, under vendored Pyodide (not the gallery) |

Manual URLs (when the server is already running):

| Page | Local URL |
|------|-----------|
| Calculator | [127.0.0.1:8000/web/pyscript/harness.html?modules=calc_graphics,calc_engine](http://127.0.0.1:8000/web/pyscript/harness.html?modules=calc_graphics,calc_engine) |

After editing files under `src/`, refresh the PyScript file manifest:

```bash
./scripts/install_refresh_manifests.sh
```

That updates `web/pyscript/micropython.toml` and `web/pyscript/pyodide.toml`, which mount `lib/` and `utils/` into the browser.

!!! tip "Port 8000"
    `mkdocs serve` also defaults to port 8000. Stop one server before starting the other, or pass a different port: `./bin/pyscript.sh calculator -p 8080`.

!!! tip "Plain http.server"
    `python -m http.server` works for static HTML but lacks the COI headers PyScript needs for some features. Prefer `./bin/pyscript.sh`.
