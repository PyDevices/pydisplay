Clone the repo. From the **repository root** (not `src/`):

```bash
./tools/pyscript.sh calculator
./tools/pyscript.sh chango
./tools/pyscript.sh                    # demo hub (index.html)
./tools/pyscript.sh calculator --no-open
```

The script runs [`tools/serve.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/serve.py) with Cross-Origin-Isolation headers required by PyScript, reuses a healthy server on port 8000 when one is already running, and opens the browser automatically.

| Page | Command | Purpose |
|------|---------|---------|
| Calculator | `./tools/pyscript.sh calculator` | Run one demo by module name |
| Chango | `./tools/pyscript.sh chango` | Manifest demo (`html/chango.json`) |
| Hub | `./tools/pyscript.sh` | Links to pages under `html/` |
| Test runner | open `http://127.0.0.1:8000/html/test.html` | Example picker |
| REPL | open `http://127.0.0.1:8000/html/repl.html` | REPL + canvas |
| Editor | open `http://127.0.0.1:8000/html/editor.html` | mpy-editor with `paint.py` |

Manual URLs (when the server is already running):

| Page | Local URL |
|------|-----------|
| Calculator | [127.0.0.1:8000/html/embed.html?modules=calculator](http://127.0.0.1:8000/html/embed.html?modules=calculator) |

After editing files under `src/`, refresh the PyScript file manifest:

```bash
./tools/regenerate.sh
```

That updates `html/pyscript.toml`, which mounts `lib/` and `add_ons/` into the browser.

!!! tip "Port 8000"
    `mkdocs serve` also defaults to port 8000. Stop one server before starting the other, or pass a different port: `./tools/pyscript.sh calculator -p 8080`.

!!! tip "Plain http.server"
    `python -m http.server` works for static HTML but lacks the COI headers PyScript needs for some features. Prefer `./tools/pyscript.sh`.
