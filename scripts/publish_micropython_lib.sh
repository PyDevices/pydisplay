#!/usr/bin/env bash
# Copy packages to the micropython-lib directory
# Install example:  mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
# Resolves to:  https://pydevices.github.io/micropython-lib/mip/PyDevices/package/6/displaysys/latest.json
# Repo URL:  https://github.com/PyDevices/micropython-lib/blob/gh-pages/mip/PyDevices/package/6/displaysys/latest.json
#
# CI / automation:
#   MICROPYTHON_LIB_DIR=../micropython-lib ./scripts/publish_micropython_lib.sh \
#     --skip-pypi --commit-message "pydisplay: Sync from abc123." --push

set -euo pipefail

SKIP_PYPI=0
DO_PUSH=0
COMMIT_MESSAGE=""
INTERACTIVE_COMMIT=0
CLI_VERSION=""

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_micropython_lib.sh [OPTION]

Copy pydisplay src/ into a local PyDevices/micropython-lib checkout, optionally
build TestPyPI wheels, then commit (and optionally push) on the PyDevices branch.

Options:
  --skip-pypi           Sync manifests only; skip hatch/twine TestPyPI uploads.
  --version X.Y.Z       Release version (overrides tag / PYDISPLAY_VERSION).
  --commit-message MSG  Commit micropython-lib changes (non-interactive).
  --push                Push micropython-lib after commit (requires credentials).
  --help, -h            Show this message.

Environment:
  MICROPYTHON_LIB_DIR   micropython-lib checkout (default: ~/github/micropython-lib)
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

DESCRIPTION_PREFIX="PyDisplay"
AUTHOR="Brad Barnett <contact@pydevices.com>"
LICENSE="MIT"

BASENAME=pydisplay
DEST_REPO="${MICROPYTHON_LIB_DIR:-$HOME/github/micropython-lib}"
SOURCE_DIR=$SOURCE_REPO/src
DEST_DIR=$DEST_REPO/micropython/$BASENAME
BUNDLE_MANIFEST=$DEST_DIR/$BASENAME-bundle/manifest.py
PYPI_DIR=$SOURCE_REPO/wheels
README_FULL_PATH=$SOURCE_REPO/README.md

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
pypi_publish_name() {
    case "$1" in
        graphics) echo "pydisplay-graphics" ;;
        *) echo "$1" ;;
    esac
}

# Representative board_config.py for micropython-lib displaysys-* example trees.
# Board configs live in nested directories; only a few desktop backends have a
# flat board_configs/<name>/board_config.py path.
displaysys_example_board_config_path() {
    local package="$1"
    local board_configs="$SOURCE_REPO/board_configs"
    case "$package" in
        displaysys-busdisplay) echo "$board_configs/busdisplay/i80/wt32sc01-plus/board_config.py" ;;
        displaysys-fbdisplay) echo "$board_configs/fbdisplay/qualia_tl040hds20/board_config.py" ;;
        displaysys-epaperdisplay) echo "$board_configs/epaperdisplay/cp_magtag/board_config.py" ;;
        displaysys-pixeldisplay) echo "$board_configs/pixeldisplay/cp_neopixel_8x8_zigzag/board_config.py" ;;
        displaysys-jndisplay) echo "$board_configs/jndisplay/board_config.py" ;;
        displaysys-pgdisplay) echo "$board_configs/pgdisplay/board_config.py" ;;
        displaysys-psdisplay) echo "$board_configs/psdisplay/board_config.py" ;;
        displaysys-sdldisplay) echo "$board_configs/sdldisplay/board_config.py" ;;
        displaysys-boarddisplay) return 1 ;;
        *) return 1 ;;
    esac
}

copy_displaysys_example_board_config() {
    local package="$1"
    local dest_dir="$2"
    local src=""

    if ! src="$(displaysys_example_board_config_path "$package")"; then
        echo "Skipping example board_config for $package"
        return 0
    fi
    if [[ ! -f "$src" ]]; then
        echo "Warning: example board_config not found for $package: $src" >&2
        return 0
    fi
    cp "$src" "$dest_dir/"
}

copy_source_tree() {
    local src="$1"
    local dest="$2"
    mkdir -p "$dest"
    rsync -a "${RSYNC_EXCLUDES[@]}" "$src/" "$dest/"
}

copy_displaysys_module() {
    local module="$1"
    local dest_dir="$2"
    local base
    base="$(basename "$module")"

    if should_skip_name "$base"; then
        return
    fi
    if [[ "$base" == *.pyc ]] || [[ "$base" == *.pyo ]]; then
        return
    fi

    mkdir -p "$dest_dir"
    if [ -d "$module" ]; then
        copy_source_tree "$module" "$dest_dir/$base"
    elif [ -f "$module" ] && [[ "$base" == *.py ]]; then
        cp "$module" "$dest_dir/"
    fi
}

prune_skipped_artifacts() {
    find "$DEST_DIR" \( \
        -type d \( -name __pycache__ -o -name .mypy_cache -o -name .ruff_cache \) \
        -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \
    \) -print0 | xargs -0 rm -rf
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

# Create the bundle manifest
mkdir -p $DEST_DIR/$BASENAME-bundle
cat <<EOF > $BUNDLE_MANIFEST
metadata(
    description="$DESCRIPTION_PREFIX bundle",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$BASENAME-bundle",
)
EOF

# Copy all the directories in $SOURCE_DIR/lib except displaysys to $DEST_DIR/$package
# Copy any example files starting with the package name to $DEST_DIR/$package/examples
for package_dir in "$SOURCE_DIR/lib"/*; do
    package=$(basename $package_dir)
    if [ -d "$package_dir" ] && [ "$package" != "displaysys" ] && ! should_skip_name "$package"; then
        echo
        echo "Processing $package"
        mkdir -p "$DEST_DIR/$package/examples"
        copy_source_tree "$package_dir" "$DEST_DIR/$package/$package"
        cp "$SOURCE_DIR/examples/$package"*.py "$DEST_DIR/$package/examples/" 2>/dev/null || true
        # write the following text to $DEST_DIR/$package/manifest.py
        cat <<EOF > $DEST_DIR/$package/manifest.py
metadata(
    description="$DESCRIPTION_PREFIX $package",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_publish_name "$package")",
)
package("$package")
EOF
        echo "require(\"$package\")" >> $BUNDLE_MANIFEST
        cp $README_FULL_PATH $DEST_DIR/$package/README.md
        if [[ "$SKIP_PYPI" -eq 0 ]]; then
            ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package $DEST_DIR/$package/manifest.py
            pushd $PYPI_DIR/$package
            build_and_upload_pypi
            popd
        fi
    fi
done

# Copy the children of displaysys to $DEST_DIR/displaysys/$package/displaysys
for module in "$SOURCE_DIR/lib/displaysys"/*; do
    base="$(basename "$module")"
    if should_skip_name "$base" || [[ "$base" == *.pyc ]] || [[ "$base" == *.pyo ]]; then
        continue
    fi
    if [[ "$base" == __init__.py ]]; then
        package=displaysys
    else
        package_dir=$(basename $module .py)
        package=displaysys-$package_dir
    fi
    echo
    echo "Processing $package"
    mkdir -p "$DEST_DIR/displaysys/$package/displaysys"
    copy_displaysys_module "$module" "$DEST_DIR/displaysys/$package/displaysys"
    mkdir -p "$DEST_DIR/displaysys/$package/examples"
    if [[ $package == displaysys ]]; then
        cat <<EOF > $DEST_DIR/displaysys/$package/manifest.py
metadata(
    description="$DESCRIPTION_PREFIX $package",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_publish_name "$package")",
)
package("displaysys")
EOF
        echo "require(\"$package\")" >> $BUNDLE_MANIFEST
        cp $README_FULL_PATH $DEST_DIR/displaysys/$package/README.md
        if [[ "$SKIP_PYPI" -eq 0 ]]; then
            ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package $DEST_DIR/displaysys/$package/manifest.py
            pushd $PYPI_DIR/$package
            build_and_upload_pypi
            popd
        fi
        cp $SOURCE_DIR/examples/$package*.py $DEST_DIR/displaysys/$package/examples/
    else
        cat <<EOF > $DEST_DIR/displaysys/$package/manifest.py
metadata(
    description="$DESCRIPTION_PREFIX $package",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$(pypi_publish_name "$package")",
)
require("displaysys")
package("displaysys")
EOF
        ## TODO:  After publishing displaysys to PyPi, uncomment the following 7 lines
        # echo "require(\"$package\")" >> $BUNDLE_MANIFEST
        # cp $README_FULL_PATH $DEST_DIR/displaysys/$package/README.md
        # ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package $DEST_DIR/displaysys/$package/manifest.py
        # pushd $PYPI_DIR/$package
        # hatch build
        # twine upload --repository testpypi dist/*
        # popd
        copy_displaysys_example_board_config "$package" "$DEST_DIR/displaysys/$package/examples/"
    fi
done

## Create the bundle file
## TODO:  Leave this commented out until the individual packages are on PyPi
# echo
# echo "Processing $BASENAME-bundle"
# cp $README_FULL_PATH $DEST_DIR/$BASENAME-bundle/README.md
# ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$BASENAME-bundle $BUNDLE_MANIFEST
# pushd $PYPI_DIR/$BASENAME-bundle
# rm -rf dist
# hatch build
# twine upload --repository testpypi dist/*
# popd

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
                git -C "$DEST_REPO" push
            fi
        fi
    fi
fi
