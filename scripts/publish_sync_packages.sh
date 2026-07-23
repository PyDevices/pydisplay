#!/usr/bin/env bash
# Sync pydisplay packages into micropython-lib and optionally upload TestPyPI wheels.
# Install example:  mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
# Resolves to:  https://pydevices.github.io/micropython-lib/mip/PyDevices/package/6/displaysys/latest.json
# Repo URL:  https://github.com/PyDevices/micropython-lib/blob/gh-pages/mip/PyDevices/package/6/displaysys/latest.json
#
# CI / automation:
#   MICROPYTHON_LIB_DIR=../micropython-lib ./scripts/publish_sync_packages.sh \
#     --skip-pypi --commit-message "pydisplay: Sync from abc123." --push

set -euo pipefail

SKIP_PYPI=0
DO_PUSH=0
COMMIT_MESSAGE=""
INTERACTIVE_COMMIT=0
CLI_VERSION=""

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_sync_packages.sh [OPTION]

Copy pydisplay src/lib packages into a local PyDevices/micropython-lib checkout,
optionally build TestPyPI wheels, then commit (and optionally push) on the
PyDevices branch.

Options:
  --skip-pypi           Sync manifests only; skip hatch/twine TestPyPI uploads.
  --version X.Y.Z       Release version (overrides tag / PYDISPLAY_VERSION).
  --commit-message MSG  Commit micropython-lib changes (non-interactive).
  --push                Push micropython-lib after commit (requires credentials).
  --help, -h            Show this message.

Environment:
  MICROPYTHON_LIB_DIR   micropython-lib checkout (default: ../micropython-lib beside this repo)
  PYDISPLAY_VERSION     Release version (overrides git tag on current commit)
  TESTPYPI_API_TOKEN    TestPyPI token for twine (when not using --skip-pypi)

Version is read from (first match): --version, PYDISPLAY_VERSION, or an exact vX.Y.Z
git tag on HEAD. Tag releases: ./scripts/publish_release_tag.sh X.Y.Z

Without --commit-message, prompts interactively when stdin is a TTY.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-pypi)
            SKIP_PYPI=1
            shift
            ;;
        --version)
            CLI_VERSION=$2
            shift 2
            ;;
        --commit-message)
            COMMIT_MESSAGE=$2
            shift 2
            ;;
        --push)
            DO_PUSH=1
            shift
            ;;
        --help | -h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$COMMIT_MESSAGE" ]] && [[ -t 0 ]]; then
    INTERACTIVE_COMMIT=1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

normalize_version() {
    local v="${1#v}"
    v="$(echo "$v" | tr -d '[:space:]')"
    if [[ ! "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
        echo "Error: invalid semver: $1 (expected X.Y.Z)" >&2
        return 1
    fi
    echo "$v"
}

resolve_version() {
    local tag=""
    if [[ -n "$CLI_VERSION" ]]; then
        normalize_version "$CLI_VERSION"
        return
    fi
    if [[ -n "${PYDISPLAY_VERSION:-}" ]]; then
        normalize_version "$PYDISPLAY_VERSION"
        return
    fi
    tag="$(git -C "$SOURCE_REPO" describe --tags --exact-match 2>/dev/null || true)"
    if [[ -n "$tag" ]]; then
        normalize_version "$tag"
        return
    fi
    echo "Error: no release version. Tag HEAD (vX.Y.Z), pass --version, or set PYDISPLAY_VERSION." >&2
    echo "  ./scripts/publish_release_tag.sh X.Y.Z   # CI release (push tag triggers publish)" >&2
    return 1
}

VERSION="$(resolve_version)" || exit 1
if [[ -z "$VERSION" ]]; then
    echo "Error: release version is empty" >&2
    exit 1
fi
echo "Release version: $VERSION"

# graphics.framebuf is generated from add_ons/framebuf.py before packaging.
"$SOURCE_REPO/scripts/install_sync_framebuf.py"

AUTHOR="Brad Barnett <contact@pydevices.com>"
LICENSE="MIT"

BASENAME=pydisplay
DEST_REPO="${MICROPYTHON_LIB_DIR:-$SOURCE_REPO/../micropython-lib}"
DEST_REPO="$(cd "$DEST_REPO" 2>/dev/null && pwd || echo "$DEST_REPO")"
export MICROPYTHON_LIB_DIR="$DEST_REPO"
SOURCE_DIR=$SOURCE_REPO/src
DEST_DIR=$DEST_REPO/micropython/$BASENAME
PYPI_DIR=$SOURCE_REPO/wheels

DISPLAY_SOURCE_DIR=$SOURCE_REPO/drivers/display
TOUCH_SOURCE_DIR=$SOURCE_REPO/drivers/touch
DISPLAY_DEST_DIR=$DEST_REPO/micropython/drivers/display
TOUCH_DEST_DIR=$DEST_REPO/micropython/drivers/touch

RSYNC_EXCLUDES=(
    --exclude '__pycache__/'
    --exclude '*.pyc'
    --exclude '*.pyo'
    --exclude '.git/'
    --exclude '.mypy_cache/'
    --exclude '.ruff_cache/'
)

should_skip_name() {
    case "$1" in
        __pycache__ | .git | .mypy_cache | .ruff_cache) return 0 ;;
        *) return 1 ;;
    esac
}

# MIP package names (eventsys, graphics, …) may differ from PyPI project names.
# TestPyPI rejects sdists for names already registered on pypi.org (e.g. graphics).
# Convention: .cursor/testpypi-naming-convention.md
pypi_publish_name() {
    case "$1" in
        graphics) echo "pydisplay-graphics" ;;
        *) echo "$1" ;;
    esac
}

# Short PyPI summary (one line) — not the monorepo tagline.
package_summary() {
    case "$1" in
        displaysys)
            echo "Cross-platform display drivers for MicroPython, CircuitPython, and CPython"
            ;;
        eventsys)
            echo "Cross-platform input events (PyGame/SDL2-style) with Runtime and device adapters"
            ;;
        multimer)
            echo "Cross-platform machine.Timer-style and asyncio timers for MicroPython and CPython"
            ;;
        graphics)
            echo "Pure-Python graphics for pydisplay (FrameBuffer, Draw, fonts); import as graphics"
            ;;
        *)
            echo "PyDisplay $1"
            ;;
    esac
}

# Package-facing README used as the TestPyPI long description.
package_readme_path() {
    local package="$1"
    echo "$SOURCE_DIR/lib/$package/README.md"
}

copy_package_readme() {
    local package="$1"
    local dest_readme="$2"
    local src_readme
    src_readme="$(package_readme_path "$package")"
    if [[ ! -f "$src_readme" ]]; then
        echo "Error: missing package README for $package: $src_readme" >&2
        echo "Add a professional package page at src/lib/$package/README.md" >&2
        exit 1
    fi
    cp "$src_readme" "$dest_readme"
}

# Extra micropython-lib require() lines for top-level pydisplay package manifests.
package_manifest_requires() {
    local package="$1"
    case "$package" in
        eventsys)
            printf '%s\n' 'require("multimer")'
            ;;
    esac
}

# multimer: no mandatory third-party PyPI deps on CPython desktop — librt (Linux),
# win32 (Windows), or threading (fallback) use the stdlib. The sdl2 backend imports
# usdl2 only when selected at runtime (_select.py); do not add usdl2 to multimer's
# manifest unless we add pip optional-extras support later.

copy_source_tree() {
    local src="$1"
    local dest="$2"
    mkdir -p "$dest"
    # --delete drops removed modules (e.g. multimer/loop.py) so the sync matches src/
    rsync -a --delete "${RSYNC_EXCLUDES[@]}" "$src/" "$dest/"
}

prune_skipped_artifacts() {
    find "$DEST_DIR" \( \
        -type d \( -name __pycache__ -o -name .mypy_cache -o -name .ruff_cache \) \
        -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \
    \) -print0 | xargs -0 rm -rf
}

# Drop packages that are no longer produced from src/ (rsync --delete only
# cleans inside each package tree, not whole package directories).
prune_stale_packages() {
    local expected_top=()
    local package_dir package name keep existing

    for package_dir in "$SOURCE_DIR/lib"/*; do
        [[ -d "$package_dir" ]] || continue
        package=$(basename "$package_dir")
        should_skip_name "$package" && continue
        expected_top+=("$package")
    done

    if [[ -d "$DEST_DIR" ]]; then
        for existing in "$DEST_DIR"/*; do
            [[ -e "$existing" ]] || continue
            name=$(basename "$existing")
            keep=0
            for package in "${expected_top[@]}"; do
                if [[ "$name" == "$package" ]]; then
                    keep=1
                    break
                fi
            done
            if [[ "$keep" -eq 0 ]]; then
                echo "Removing stale package tree: $existing"
                rm -rf "$existing"
            fi
        done
    fi

    # displaysys is a single full package; drop any leftover displaysys-* backends.
    if [[ -d "$DEST_DIR/displaysys" ]]; then
        for existing in "$DEST_DIR/displaysys"/*; do
            [[ -e "$existing" ]] || continue
            name=$(basename "$existing")
            if [[ "$name" != "displaysys" ]]; then
                echo "Removing stale displaysys package: $existing"
                rm -rf "$existing"
            fi
        done
    fi
}

build_and_upload_pypi() {
    if [[ "$SKIP_PYPI" -eq 1 ]]; then
        return 0
    fi
    rm -rf dist
    hatch build
    if [[ -n "${TESTPYPI_API_TOKEN:-}" ]]; then
        TWINE_USERNAME=__token__ TWINE_PASSWORD="$TESTPYPI_API_TOKEN" \
            twine upload --repository testpypi --verbose dist/*
    else
        twine upload --repository testpypi --verbose dist/*
    fi
}

# Concurrent tag publishes from sibling repos share micropython-lib PyDevices.
push_micropython_lib() {
    local repo="$1"
    local branch
    branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
    local max_attempts=8
    local attempt=1
    while true; do
        if git -C "$repo" push origin "HEAD:${branch}"; then
            return 0
        fi
        if (( attempt >= max_attempts )); then
            echo "Error: push to micropython-lib ${branch} failed after ${max_attempts} attempts" >&2
            return 1
        fi
        echo "Push rejected (likely concurrent publish); rebase onto origin/${branch} and retry (${attempt}/${max_attempts})..."
        git -C "$repo" fetch origin "${branch}"
        if ! git -C "$repo" rebase "origin/${branch}"; then
            git -C "$repo" rebase --abort 2>/dev/null || true
            git -C "$repo" fetch --deepen=100 origin "${branch}" || git -C "$repo" fetch --unshallow origin || true
            git -C "$repo" rebase "origin/${branch}"
        fi
        attempt=$((attempt + 1))
        sleep "$attempt"
    done
}

# Copy all the directories in $SOURCE_DIR/lib except displaysys to $DEST_DIR/$package
for package_dir in "$SOURCE_DIR/lib"/*; do
    package=$(basename $package_dir)
    if [ -d "$package_dir" ] && [ "$package" != "displaysys" ] && ! should_skip_name "$package"; then
        echo
        echo "Processing $package"
        copy_source_tree "$package_dir" "$DEST_DIR/$package/$package"
        extra_requires="$(package_manifest_requires "$package")"
        # write the following text to $DEST_DIR/$package/manifest.py
        cat <<EOF > $DEST_DIR/$package/manifest.py
metadata(
    description="$(package_summary "$package")",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_publish_name "$package")",
)
${extra_requires}
package("$package")
EOF
        copy_package_readme "$package" "$DEST_DIR/$package/README.md"
        if [[ "$SKIP_PYPI" -eq 0 ]]; then
            ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package $DEST_DIR/$package/manifest.py
            pushd $PYPI_DIR/$package
            build_and_upload_pypi
            popd
        fi
    fi
done

# displaysys: full tree (all backends). One MIP/TestPyPI package.
# board_config.py is not included — install a board_configs/*/ package instead.
echo
echo "Processing displaysys (full package)"
mkdir -p "$DEST_DIR/displaysys/displaysys"
copy_source_tree "$SOURCE_DIR/lib/displaysys" "$DEST_DIR/displaysys/displaysys/displaysys"
rm -f "$DEST_DIR/displaysys/displaysys/displaysys/boarddisplay.py"
cat <<EOF > $DEST_DIR/displaysys/displaysys/manifest.py
metadata(
    description="$(package_summary "displaysys")",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_publish_name "displaysys")",
)
package("displaysys")
EOF
copy_package_readme "displaysys" "$DEST_DIR/displaysys/displaysys/README.md"
if [[ "$SKIP_PYPI" -eq 0 ]]; then
    ./scripts/publish_make_pyproject.py --output $PYPI_DIR/displaysys $DEST_DIR/displaysys/displaysys/manifest.py
    pushd $PYPI_DIR/displaysys
    build_and_upload_pypi
    popd
fi

prune_stale_packages
prune_skipped_artifacts

if [[ "$INTERACTIVE_COMMIT" -eq 1 ]] || [[ -n "$COMMIT_MESSAGE" ]]; then
    if [[ "$INTERACTIVE_COMMIT" -eq 1 ]] && [[ -z "$COMMIT_MESSAGE" ]]; then
        echo
        echo "To commit changes now, enter your git commit message, otherwise, press enter."
        echo "The commit should be in the format:  '$BASENAME:  At least two words and a period.'"
        read -r -p "Enter your git commit message: " commit_message
        COMMIT_MESSAGE=$commit_message
    fi
    if [[ -n "$COMMIT_MESSAGE" ]]; then
        if git -C "$DEST_REPO" diff --quiet && git -C "$DEST_REPO" diff --cached --quiet; then
            echo "No changes to commit in $DEST_REPO"
        else
            git -C "$DEST_REPO" add .
            git -C "$DEST_REPO" commit -s -m "$COMMIT_MESSAGE"
            if [[ "$DO_PUSH" -eq 1 ]]; then
                push_micropython_lib "$DEST_REPO"
            fi
        fi
    fi
fi
