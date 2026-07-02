#!/usr/bin/env bash
# Link tools/typings/lvgl.pyi beside the installed lvgl-cpython binary in .venv.
# Re-run after: pip install --force-reinstall lvgl-cpython
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_SITE="${ROOT}/.venv/lib/python3.12/site-packages"
STUB="${ROOT}/tools/typings/lvgl.pyi"
TARGET="${VENV_SITE}/lvgl.pyi"

if [[ ! -f "${STUB}" ]]; then
  echo "missing stub: ${STUB}" >&2
  exit 1
fi
if [[ ! -d "${VENV_SITE}" ]]; then
  echo "missing venv site-packages: ${VENV_SITE}" >&2
  exit 1
fi
ln -sf ../../../../tools/typings/lvgl.pyi "${TARGET}"
echo "linked ${TARGET} -> tools/typings/lvgl.pyi"
