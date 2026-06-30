#!/usr/bin/env bash
# Build mip/PyDevices from micropython-lib and push to gh-pages.
#
# Requires:
#   MICROPYTHON_LIB_DIR   checkout of PyDevices/micropython-lib (PyDevices branch)
#   PYDISPLAY_DIR         pydisplay repo root (default: parent of scripts/)
#
# Optional:
#   MICROPYTHON_DIR       micropython source for mpy-cross (default: /tmp/micropython)
#   MIP_INDEX_OUTPUT      build output dir (default: /tmp/mip-index)
#   MIP_INDEX_SUBDIR      gh-pages subdir under mip/ (default: PyDevices)
#   GITHUB_SHA            used in commit message (Actions sets this)
#
# Push credentials: configure git remote on MICROPYTHON_LIB_DIR before calling
# (see .github/workflows/publish-micropython-lib.yml).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYDISPLAY_DIR="${PYDISPLAY_DIR:-$ROOT}"
LIB_DIR="${MICROPYTHON_LIB_DIR:?set MICROPYTHON_LIB_DIR}"
MPY_DIR="${MICROPYTHON_DIR:-/tmp/micropython}"
INDEX_OUT="${MIP_INDEX_OUTPUT:-/tmp/mip-index}"
MIP_SUBDIR="${MIP_INDEX_SUBDIR:-PyDevices}"
MPY_CROSS="$MPY_DIR/mpy-cross/build/mpy-cross"
PAGES_PATH="${MIP_GHPAGES_WORKTREE:-/tmp/micropython-lib-gh-pages}"

if [[ ! -x "$MPY_CROSS" ]]; then
    echo "Building mpy-cross in $MPY_DIR"
    if [[ ! -d "$MPY_DIR/.git" ]]; then
        git clone --depth=1 https://github.com/micropython/micropython.git "$MPY_DIR"
    fi
    make -C "$MPY_DIR/mpy-cross" -j"$(nproc)" CFLAGS_EXTRA=-O0
fi

rm -rf "$INDEX_OUT"
mkdir -p "$INDEX_OUT"

echo "Compiling MIP index from $LIB_DIR -> $INDEX_OUT"
python3 "$PYDISPLAY_DIR/scripts/build.py" \
    --lib-dir "$LIB_DIR" \
    --micropython "$MPY_DIR" \
    --mpy-cross "$MPY_CROSS" \
    --output "$INDEX_OUT"

cd "$LIB_DIR"
git config user.name 'github-actions[bot]'
git config user.email 'github-actions[bot]@users.noreply.github.com'

NEW_BRANCH=0
if git fetch --depth=1 origin gh-pages; then
    if git worktree list | grep -q "$PAGES_PATH"; then
        git worktree remove --force "$PAGES_PATH" || true
    fi
    git worktree add "$PAGES_PATH" gh-pages
else
    echo "Creating gh-pages branch..."
    git worktree add --force "$PAGES_PATH" HEAD
    cd "$PAGES_PATH"
    git switch --orphan gh-pages
    NEW_BRANCH=1
    cd "$LIB_DIR"
fi

DEST_PATH="$PAGES_PATH/mip/$MIP_SUBDIR"
rm -rf "$DEST_PATH"
mkdir -p "$DEST_PATH"
cp -r "$INDEX_OUT/." "$DEST_PATH/"

cd "$PAGES_PATH"
git add .
SHA="${GITHUB_SHA:-local}"
git diff --staged --quiet && {
    echo "No MIP index changes to publish"
    exit 0
}
git commit -m "pydisplay: Update mip/$MIP_SUBDIR from PyDevices/pydisplay ${SHA}."

if [[ "$NEW_BRANCH" -eq 0 ]]; then
    git pull --rebase origin gh-pages
fi
git push origin gh-pages

echo "Published https://PyDevices.github.io/micropython-lib/mip/$MIP_SUBDIR"
