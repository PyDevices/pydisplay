#!/bin/env bash
# Copy packages to the micropython-lib directory
# Install example:  mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
# Resolves to:  https://pydevices.github.io/micropython-lib/mip/PyDevices/package/6/displaysys/latest.json
# Repo URL:  https://github.com/PyDevices/micropython-lib/blob/gh-pages/mip/PyDevices/package/6/displaysys/latest.json

VERSION=0.0.2
DESCRIPTION_PREFIX="PyDisplay"
AUTHOR="Brad Barnett <contact@pydevices.com>"
LICENSE="MIT"

BASENAME=pydisplay
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
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
    rm -rf dist
    hatch build
    twine upload --repository testpypi dist/*
}

# set -e

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
    pypi_publish="$package",
)
package("$package")
EOF
        echo "require(\"$package\")" >> $BUNDLE_MANIFEST
        cp $README_FULL_PATH $DEST_DIR/$package/README.md
        ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package $DEST_DIR/$package/manifest.py
        pushd $PYPI_DIR/$package
        build_and_upload_pypi
        popd
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
    pypi_publish="$package",
)
package("displaysys")
EOF
        echo "require(\"$package\")" >> $BUNDLE_MANIFEST
        cp $README_FULL_PATH $DEST_DIR/displaysys/$package/README.md
        ./scripts/publish_make_pyproject.py --output $PYPI_DIR/$package  $DEST_DIR/displaysys/$package/manifest.py
        pushd $PYPI_DIR/$package
        build_and_upload_pypi
        popd
        cp $SOURCE_DIR/examples/$package*.py $DEST_DIR/displaysys/$package/examples/
    else
        cat <<EOF > $DEST_DIR/displaysys/$package/manifest.py
metadata(
    description="$DESCRIPTION_PREFIX $package",
    version="$VERSION",
    author="$AUTHOR",
    license="$LICENSE",
    pypi_publish="$package",
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
        if [[ $package == displaysys-busdisplay ]]; then
            cp $SOURCE_DIR/../board_configs/busdisplay/i80/wt32sc01-plus/board_config.py $DEST_DIR/displaysys/$package/examples/
        else
            if [[ $package == displaysys-fbdisplay ]]; then
                cp $SOURCE_DIR/../board_configs/fbdisplay/qualia_tl040hds20/board_config.py $DEST_DIR/displaysys/$package/examples/
            else
                cp $SOURCE_DIR/../board_configs/$package_dir/board_config.py $DEST_DIR/displaysys/$package/examples/
            fi
        fi
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

echo
echo "To commit changes now, enter your git commit message, otherwise, press enter."
echo "The commit should be in the format:  '$BASENAME:  At least two words and a period.'"
read -p "Enter your git commit message: " commit_message
if [ -n "$commit_message" ]; then
    git -C $DEST_REPO add .
    git -C $DEST_REPO commit -s -m "$commit_message"
    git -C $DEST_REPO push
fi
