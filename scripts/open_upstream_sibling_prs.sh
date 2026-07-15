#!/usr/bin/env bash
# Prepare and push upstream PR branches for palettes / pdwidgets.
# Requires write access to PyDevices/palettes and PyDevices/pdwidgets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${PYDISPLAY_SIBLINGS_DIR:-/tmp/pydevices-siblings-pr}"

open_repo_pr() {
  local name="$1" branch="$2" patch="$3" title="$4" body_file="$5"
  local dir="$WORK/$name"

  if [[ -d "$dir/.git" ]]; then
    git -C "$dir" fetch origin main
    git -C "$dir" checkout -q main
    git -C "$dir" reset --hard -q origin/main
  else
    mkdir -p "$WORK"
    git clone --depth 1 "https://github.com/PyDevices/${name}.git" "$dir"
  fi

  git -C "$dir" checkout -B "$branch"
  patch -p1 -d "$dir" -N <"$patch" || true
  git -C "$dir" add -A
  if git -C "$dir" diff --cached --quiet; then
    echo "$name: no changes (patch already applied?)"
    return 0
  fi
  git -C "$dir" commit -m "$title"
  git -C "$dir" push -u origin "$branch"
  gh pr create \
    --repo "PyDevices/${name}" \
    --base main \
    --head "$branch" \
    --title "$title" \
    --body-file "$body_file" \
    --draft
}

open_repo_pr palettes \
  cursor/micropython-zip-strict-0555 \
  "$ROOT/patches/palettes/micropython-zip-strict.patch" \
  "Fix material_design palette on MicroPython and CircuitPython" \
  "$ROOT/patches/palettes/PR_BODY.md"

open_repo_pr pdwidgets \
  cursor/micropython-compat-0555 \
  "$ROOT/patches/pdwidgets/pdwidgets-fixes.patch" \
  "MicroPython/CircuitPython compatibility and CPython 3.12 fixes" \
  "$ROOT/patches/pdwidgets/PR_BODY.md"

echo "Done. Check PyDevices/palettes and PyDevices/pdwidgets for new draft PRs."
