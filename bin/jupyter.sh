#!/usr/bin/env bash
# Run pydevices-examples applications in Jupyter (desktop / ipywidgets).
#
# Mirrors the primary CLI shapes of unix/micropython.exe:
#
#   micropython [<opts>] [-c <command> | -m <module> | <filename>]
#   micropython -i …    # REPL after running command/module/file
#
# Usage (from repo root):
#   ./bin/jupyter.sh examples/pydevices_demo.py
#   ./bin/jupyter.sh -m examples.chango
#   ./bin/jupyter.sh                          # open lib/jupyter_notebook.ipynb (hub)
#   ./bin/jupyter.sh examples/pydevices_demo.py --cursor  # open generated notebook in Cursor
#   ./bin/jupyter.sh examples/pydevices_demo.py --no-open # generate notebook / start server only
#
# Browser mode starts JupyterLab with notebook-dir=lib/ (see docs/platforms/jupyter-run.md).
# Cursor mode skips the server and opens the notebook in the editor.
#
# Generated notebooks are always interactive Jupyter sessions (extra cells
# can be run against the live kernel), so -i does not need a separate
# run-then-REPL step the way a script interpreter would. Notebook runs use a
# shared scratch directory outside the repo for board_config installs.

set -euo pipefail

# Resolve symlinks so ~/bin/jupyter.sh → …/pydevices-examples/bin/jupyter.sh finds the repo.
_SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PYDEVICES_EXAMPLES_ROOT="${PYDEVICES_EXAMPLES_ROOT:-$(cd "$_SCRIPT_DIR/.." && pwd)}"
SRC="$PYDEVICES_EXAMPLES_ROOT/lib"
HUB_NOTEBOOK="$SRC/jupyter_notebook.ipynb"
VENV="${JUPYTER_VENV:-$PYDEVICES_EXAMPLES_ROOT/.venv}"
DESKTOP_BOARD_CONFIG_MIP="github:PyDevices/pydevices/board_configs/desktop/package.json"
PYDEVICES_MIP_INDEX="https://PyDevices.github.io/micropython-lib/mip/PyDevices"
TESTPYPI_INDEX="https://test.pypi.org/simple/"
PORT=8888
FILE_ARG=""
MODULE_ARG=""
CODE_ARG=""
ENTRY_KIND=""    # file | module | code | ""
INTERACTIVE=0
OPEN=1
USE_CURSOR=0

usage() {
  cat <<EOF
Usage: ./bin/jupyter.sh [<opts>] [-c <code> | -m <module> | <file>]
       ./bin/jupyter.sh -i [<opts>]

Mirrors micropython/micropython.exe's primary CLI shapes.

  <file>            generate + open a notebook that runs examples/<name>.py
                     (must be a file — a directory errors; use -m for packages)
  -m <module>       generate + open a notebook that runs examples.<name> or
                     <name> (module or package under lib/examples/). NOT a
                     bare directory path.
  -c <code>         generate + open a notebook whose run cell is exactly
                     this code string (no examples import)
  -i                accepted as a no-op: generated notebooks already run
                     against a live kernel, so there's no separate
                     run-then-REPL step. Alone (no other entry), same as
                     no args: open the hub notebook.
  (nothing)         open the hub notebook (lib/jupyter_notebook.ipynb)

  --cursor          open in Cursor (no JupyterLab server)
  -p, --port PORT   JupyterLab port (default: 8888)
  --no-open         prepare notebook / server but do not open UI
  -h, --help        this help

Generated notebooks import via \`from examples import <name>\` (or
\`import examples.<a>.<b>\` for nested files) — never a bare \`import <name>\`
and never a path-bootstrap cell. If PYTHONPATH is unset, jupyter.sh exports
PYTHONPATH=".:lib:utils" plus sibling pydevices ``lib`` / ``utils`` /
``drivers/display`` for the JupyterLab/kernel process (cwd=lib) so
\`import displaydev\`, \`import mip\`, etc. resolve without a bootstrap cell.
Run notebooks also ensure a Jupyter board config is available by calling
\`mip.install("${DESKTOP_BOARD_CONFIG_MIP}", target=".")\` when
\`import board_config\` fails.

The Jupyter environment itself must already have any example dependencies
installed before `jupyter.sh` is launched.

Environment:
  PYDEVICES_EXAMPLES_ROOT    pydevices-examples clone (default: parent of bin/)
  JUPYTER_VENV      Python venv with jupyter deps (default: .venv)

Examples:
  ./bin/jupyter.sh examples/pydevices_demo.py
  ./bin/jupyter.sh -m examples.chango
  ./bin/jupyter.sh examples/pydevices_demo.py --cursor
  ./bin/jupyter.sh -c "from examples import chango"

Requires (in JUPYTER_VENV):
  pip install pillow ipywidgets ipyevents jupyterlab
EOF
}

set_entry() {
  local kind="$1"
  if [[ -n "$ENTRY_KIND" && "$ENTRY_KIND" != "$kind" ]]; then
    echo "jupyter.sh: cannot combine a ${ENTRY_KIND} entry with a ${kind} entry" >&2
    exit 1
  fi
  ENTRY_KIND="$kind"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -m)
      MODULE_ARG="${2:?-m requires a module name}"
      set_entry module
      shift 2
      ;;
    -c)
      CODE_ARG="${2:?-c requires a command string}"
      set_entry code
      shift 2
      ;;
    -i)
      INTERACTIVE=1
      shift
      ;;
    --cursor)
      USE_CURSOR=1
      shift
      ;;
    -p|--port)
      PORT="${2:?--port requires a number}"
      shift 2
      ;;
    --no-open)
      OPEN=0
      shift
      ;;
    -*)
      echo "jupyter.sh: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$FILE_ARG" ]]; then
        echo "jupyter.sh: unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      FILE_ARG="$1"
      set_entry file
      shift
      ;;
  esac
done

if [[ ! -d "$SRC" ]]; then
  echo "jupyter.sh: pydevices-examples lib/ not found under $PYDEVICES_EXAMPLES_ROOT" >&2
  exit 1
fi

if [[ -z "${PYTHONPATH:-}" ]]; then
  HW="$(cd "$PYDEVICES_EXAMPLES_ROOT/../pydevices" 2>/dev/null && pwd || true)"
  HW_PATH=""
  if [[ -n "$HW" && -d "$HW/utils" ]]; then
    HW_PATH=":$HW/lib:$HW/utils:$HW/drivers/display"
  fi
  export PYTHONPATH=".:lib:utils${HW_PATH}"
  echo "jupyter.sh: PYTHONPATH unset; exporting PYTHONPATH=$PYTHONPATH for the kernel (cwd=$SRC)" >&2
fi

jupyter_bin() {
  if [[ -x "$VENV/bin/jupyter" ]]; then
    echo "$VENV/bin/jupyter"
    return 0
  fi
  if command -v jupyter >/dev/null 2>&1; then
    command -v jupyter
    return 0
  fi
  return 1
}

ensure_jupyter_deps() {
  if [[ -x "$VENV/bin/python" ]]; then
    return 0
  fi
  cat >&2 <<EOF
jupyter.sh: Jupyter venv not found: $VENV

Create it from the pydevices-examples repo root:

  cd $PYDEVICES_EXAMPLES_ROOT
  python3 -m venv .venv
  .venv/bin/pip install pillow ipywidgets ipyevents jupyterlab

Or set JUPYTER_VENV to an existing environment.
EOF
  exit 1
}

# Given a dotted path *relative to examples* (e.g. "chango" or
# "apollo.apollo"), print the import statement for the run cell:
#   single component -> from examples import <name>
#   nested            -> import examples.<a>.<b>
# followed by a filesystem-safe slug (dots -> underscores) for the notebook filename.
emit_entry() {
  local dotted="$1"
  local slug="${dotted//./_}"
  case "$dotted" in
    *.*) printf 'import examples.%s\n' "$dotted" ;;
    *)   printf 'from examples import %s\n' "$dotted" ;;
  esac
  printf '%s\n' "$slug"
}

extract_header_deps() {
  local file_path="$1"
  DEPS_FILE="$file_path" "$VENV/bin/python" <<'PY'
import os

path = os.environ["DEPS_FILE"]
deps = []
try:
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            s = line.strip()
            if s.startswith("# deps:"):
                body = s.split(":", 1)[1].strip()
                deps = [part.strip() for part in body.split(",") if part.strip()]
                break
except OSError:
    pass
print(",".join(deps))
PY
}

map_wheel_deps() {
  local deps_csv="$1"
  if [[ -z "$deps_csv" ]]; then
    printf '\n'
    return 0
  fi
  PYDEVICES_EXAMPLES_ROOT="$PYDEVICES_EXAMPLES_ROOT" DEPS_CSV="$deps_csv" "$VENV/bin/python" <<'PY'
import os
import sys
from urllib.parse import parse_qs

root = os.environ["PYDEVICES_EXAMPLES_ROOT"]
deps_csv = os.environ.get("DEPS_CSV", "")
deps = tuple(d.strip() for d in deps_csv.split(",") if d.strip())
sys.path.insert(0, os.path.join(root, "scripts"))
import url_maker  # noqa: E402

query = url_maker.urls_from_deps(deps=deps, runtime="pyodide")
parsed = parse_qs(query.lstrip("?"))
deps_out = parsed.get("deps", [""])[0]
print(deps_out)
PY
}

# -m examples.<name> or -m <name> — top-level module/package under
# lib/examples/, or a dotted path to a file nested in an example package.
resolve_module_target() {
  local mod="$1"

  if [[ "$mod" == */* || "$mod" == /* ]]; then
    echo "jupyter.sh: -m takes a dotted module name (e.g. -m examples.chango), not a path: $mod" >&2
    return 1
  fi

  local rest="$mod"
  case "$rest" in
    examples.*) rest="${rest#examples.}" ;;
    examples)
      echo "jupyter.sh: module name required after 'examples' (e.g. -m examples.chango)" >&2
      return 1
      ;;
  esac

  local relpath="${rest//./\/}"
  local source_file=""
  if [[ -f "$SRC/examples/${relpath}.py" ]]; then
    source_file="$SRC/examples/${relpath}.py"
  elif [[ -f "$SRC/examples/${relpath}/__init__.py" ]]; then
    source_file="$SRC/examples/${relpath}/__init__.py"
  fi
  if [[ -n "$source_file" ]]; then
    emit_entry "$rest"
    printf '%s\n' "$source_file"
    return 0
  fi

  echo "jupyter.sh: no such module: examples.${rest}" >&2
  return 1
}

# <file> — must live under lib/examples/ (a directory errors: use -m for packages).
resolve_file_target() {
  local file="$1"
  local resolved=""

  if [[ "$file" == /* ]]; then
    resolved="$file"
  elif [[ -e "$file" ]]; then
    resolved="$(cd "$(dirname -- "$file")" && pwd)/$(basename -- "$file")"
  elif [[ -e "$SRC/$file" ]]; then
    resolved="$SRC/$file"
  else
    echo "jupyter.sh: no such file: $file" >&2
    return 1
  fi

  if [[ -d "$resolved" ]]; then
    echo "jupyter.sh: $file: Is a directory (use -m examples.<name> to run a package)" >&2
    return 1
  fi
  if [[ ! -f "$resolved" ]]; then
    echo "jupyter.sh: no such file: $file" >&2
    return 1
  fi

  local rel=""
  case "$resolved" in
    "$SRC"/*) rel="${resolved#"$SRC"/}" ;;
    *)
      echo "jupyter.sh: '$file' is outside pydevices-examples lib/ — jupyter.sh can only launch example modules (examples/<name>.py)" >&2
      return 1
      ;;
  esac

  case "$rel" in
    examples/*.py)
      local mid="${rel#examples/}"
      mid="${mid%.py}"
      emit_entry "${mid//\//.}"
      printf '%s\n' "$resolved"
      ;;
    *)
      echo "jupyter.sh: '$file' is not under examples/ — jupyter.sh can only launch example modules (examples/<name>.py)" >&2
      return 1
      ;;
  esac
}

write_run_notebook() {
  local title="$1"
  local out="$2"
  local run_source="$3"
  local wheel_deps_csv="$4"

  mkdir -p "$(dirname "$out")"
  TITLE="$title" OUT="$out" RUN_SOURCE="$run_source" WHEEL_DEPS="$wheel_deps_csv" BOARD_CONFIG_MIP="$DESKTOP_BOARD_CONFIG_MIP" MIP_INDEX="$PYDEVICES_MIP_INDEX" TESTPYPI_INDEX="$TESTPYPI_INDEX" "$VENV/bin/python" <<'PY'
import json
import os
from pathlib import Path

title = os.environ["TITLE"]
out = Path(os.environ["OUT"])
run_source = os.environ["RUN_SOURCE"]
board_config_mip = os.environ["BOARD_CONFIG_MIP"]
mip_index = os.environ["MIP_INDEX"]
wheel_deps = [d.strip() for d in os.environ.get("WHEEL_DEPS", "").split(",") if d.strip()]
testpypi_index = os.environ["TESTPYPI_INDEX"]

bootstrap = [
  "import os",
    "import sys",
    "from pathlib import Path",
    "",
    "# Ensure desktop board_config is present for notebook runs.",
  "scratch = Path(os.environ.get('PYDEVICES_JUPYTER_SCRATCH', Path.home() / '.cache' / 'pydevices-examples' / 'jupyter'))",
    "scratch.mkdir(parents=True, exist_ok=True)",
    "sys.path.insert(0, str(scratch))",
    "try:",
    "    import board_config  # noqa: F401",
    "except ImportError:",
    "    import mip",
    f'    mip.install(',
    f'        "{board_config_mip}",',
    f'        index="{mip_index}",',
    f'        target=str(scratch),',
    f'    )',
    "    import board_config  # noqa: F401",
    "",
]

run_lines = [line + "\n" for line in (bootstrap + run_source.splitlines())] or ["\n"]
run_lines[-1] = run_lines[-1].rstrip("\n")

deps_lines = None
if wheel_deps:
    deps_lines = [
        "# Install dependencies into the selected kernel",
        "import pip",
        f"pip.main(['install', '-i', '{testpypi_index}', *{repr(wheel_deps)}])",
    ]
    deps_lines = [line + "\n" for line in deps_lines]
    deps_lines[-1] = deps_lines[-1].rstrip("\n")

cells = [
    {
        "cell_type": "markdown",
        "id": "intro",
        "metadata": {},
        "source": [
            f"# pydevices-examples — {title}\n",
            "\n",
            "Generated by `./bin/jupyter.sh`. Click the **ipywidgets Image** for touch input.\n",
            "\n",
            "**Cursor / VS Code:** select the `.venv` kernel, then run all cells.\n",
            "**Stop:** Kernel → Restart (async examples run in the background).\n",
        ],
    },
    {
        "cell_type": "code",
        "id": "run",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": run_lines,
    },
]

if deps_lines:
    cells.insert(
        1,
        {
            "cell_type": "code",
            "id": "deps",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": deps_lines,
        },
    )

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    },
    "cells": cells,
}

out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print(out)
PY
}

open_url() {
  local url="$1"
  if [[ "$OPEN" -eq 0 ]]; then
    return 0
  fi
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v wslview >/dev/null 2>&1; then
    wslview "$url" >/dev/null 2>&1 &
  elif [[ -n "${WSL_DISTRO_NAME:-}" ]] && command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "$url" >/dev/null 2>&1 &
  else
    echo "jupyter.sh: no browser opener found; open manually:"
    echo "  $url"
  fi
}

open_cursor() {
  local path="$1"
  local editor="${CURSOR:-cursor}"
  if [[ "$OPEN" -eq 0 ]]; then
    return 0
  fi
  if ! command -v "$editor" >/dev/null 2>&1; then
    echo "jupyter.sh: $editor not found in PATH (set CURSOR to override)" >&2
    echo "jupyter.sh: notebook: $path" >&2
    exit 1
  fi
  "$editor" "$path" >/dev/null 2>&1 &
}

server_ready() {
  curl -sf -o /dev/null "http://127.0.0.1:${PORT}/api/status" 2>/dev/null
}

server_healthy() {
  server_ready && curl -sf -o /dev/null "http://127.0.0.1:${PORT}/lab" 2>/dev/null
}

stop_server_on_port() {
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti :"${PORT}" 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
    sleep 0.5
    return 0
  fi
  if [[ -n "$pids" ]]; then
    echo "jupyter.sh: stopping server on port ${PORT}"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 0.5
  fi
}

wait_for_server() {
  local i
  for i in $(seq 1 80); do
    if server_healthy; then
      return 0
    fi
    sleep 0.15
  done
  return 1
}

NOTEBOOK=""
SLUG=""
if [[ -n "$ENTRY_KIND" ]]; then
  ensure_jupyter_deps
  WHEEL_DEPS_CSV=""
  case "$ENTRY_KIND" in
    code)
      SLUG="code"
      TITLE="inline code"
      RUN_SOURCE="$CODE_ARG"
      ;;
    module)
      OUT="$(resolve_module_target "$MODULE_ARG")" || exit 1
      mapfile -t _lines <<<"$OUT"
      RUN_SOURCE="${_lines[0]}"
      SLUG="${_lines[1]}"
      SRC_FILE="${_lines[2]:-}"
      if [[ -n "$SRC_FILE" ]]; then
        HEADER_DEPS="$(extract_header_deps "$SRC_FILE")"
        WHEEL_DEPS_CSV="$(map_wheel_deps "$HEADER_DEPS")"
      fi
      TITLE="$SLUG"
      ;;
    file)
      OUT="$(resolve_file_target "$FILE_ARG")" || exit 1
      mapfile -t _lines <<<"$OUT"
      RUN_SOURCE="${_lines[0]}"
      SLUG="${_lines[1]}"
      SRC_FILE="${_lines[2]:-}"
      if [[ -n "$SRC_FILE" ]]; then
        HEADER_DEPS="$(extract_header_deps "$SRC_FILE")"
        WHEEL_DEPS_CSV="$(map_wheel_deps "$HEADER_DEPS")"
      fi
      TITLE="$SLUG"
      ;;
  esac
  NOTEBOOK="$SRC/run-${SLUG}.ipynb"
  write_run_notebook "$TITLE" "$NOTEBOOK" "$RUN_SOURCE" "$WHEEL_DEPS_CSV" >/dev/null
  echo "jupyter.sh: wrote $NOTEBOOK"
else
  NOTEBOOK="$HUB_NOTEBOOK"
  if [[ ! -f "$NOTEBOOK" ]]; then
    echo "jupyter.sh: hub notebook not found: $NOTEBOOK" >&2
    exit 1
  fi
fi

if [[ "$USE_CURSOR" -eq 1 ]]; then
  echo "jupyter.sh: opening in Cursor — select kernel $VENV/bin/python, run all cells"
  open_cursor "$NOTEBOOK"
  echo "jupyter.sh: $NOTEBOOK"
  exit 0
fi

ensure_jupyter_deps
JUPYTER="$(jupyter_bin)"

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

BASE="http://127.0.0.1:${PORT}"
# Path relative to notebook-dir (src/)
if [[ -n "$ENTRY_KIND" ]]; then
  LAB_PATH="run-${SLUG}.ipynb"
else
  LAB_PATH="jupyter_notebook.ipynb"
fi
URL="${BASE}/lab/tree/${LAB_PATH}"

if server_healthy; then
  echo "jupyter.sh: reusing JupyterLab at ${BASE}"
else
  if server_ready; then
    echo "jupyter.sh: replacing unhealthy JupyterLab on port ${PORT}" >&2
    stop_server_on_port
  fi
  echo "jupyter.sh: starting JupyterLab on ${BASE} (notebook-dir=${SRC})"
  "$JUPYTER" lab \
    --no-browser \
    --notebook-dir="$SRC" \
    --port="$PORT" \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --ServerApp.disable_check_xsrf=True \
    &
  SERVER_PID=$!
  if ! wait_for_server; then
    echo "jupyter.sh: JupyterLab did not become ready on ${BASE}" >&2
    exit 1
  fi
  if ! server_healthy; then
    echo "jupyter.sh: JupyterLab started but /lab is not healthy — check ${VENV}/bin/jupyter" >&2
    exit 1
  fi
fi

echo "jupyter.sh: ${URL}"
echo "jupyter.sh: kernel: ${VENV}/bin/python"
open_url "$URL"

if [[ -n "$SERVER_PID" ]]; then
  echo "jupyter.sh: Ctrl+C to stop JupyterLab"
  wait "$SERVER_PID"
fi
