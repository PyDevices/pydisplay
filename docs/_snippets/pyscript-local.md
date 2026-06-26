Clone the repo. From the **repository root** (not `src/`):

```bash
python -m http.server
```

Open [http://localhost:8000/](http://localhost:8000/) — the hub links to pages under `html/`.

| Page | Local URL | Purpose |
|------|-----------|---------|
| Calculator | [localhost:8000/html/?modules=calculator](http://localhost:8000/html/?modules=calculator) | Run one demo by name |
| Test runner | [localhost:8000/html/test.html](http://localhost:8000/html/test.html) | Example picker |
| REPL | [localhost:8000/html/repl.html](http://localhost:8000/html/repl.html) | REPL + canvas |
| Editor | [localhost:8000/html/editor.html](http://localhost:8000/html/editor.html) | mpy-editor with `paint.py` |

After editing files under `src/`, refresh the PyScript file manifest:

```bash
./tools/regenerate.sh
```

That updates `html/pyscript.toml`, which mounts `lib/` and `add_ons/` into the browser.

!!! tip "Port 8000"
    `mkdocs serve` also defaults to port 8000. Stop one server before starting the other, or pass a different port: `python -m http.server 8080`.
