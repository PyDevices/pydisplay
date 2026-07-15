#!/usr/bin/env bash
# Compute the next release version for this repo.
#
#   With existing vX.Y.Z tags — highest tag + 1 patch (e.g. v0.0.1 -> 0.0.2).
#     Non-semver / pre-release tags (e.g. v1.2.3-rc1) are ignored.
#   With no vX.Y.Z tags — base version from the first match of setup.py
#     RELEASE_VERSION, pyproject.toml [project] version, a VERSION file, else 0.0.1.
#
# Usage:
#   ./scripts/next_release_version.sh
#   ./scripts/next_release_version.sh --verbose

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

VERBOSE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose | -v)
            VERBOSE=1
            shift
            ;;
        --help | -h)
            sed -n '2,12p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

read_base_version() {
    local v=""
    if [[ -f "$SOURCE_REPO/setup.py" ]]; then
        v="$(grep -E '^\s*RELEASE_VERSION\s*=' "$SOURCE_REPO/setup.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
        [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && {
            echo "$v"
            return 0
        }
    fi
    if [[ -f "$SOURCE_REPO/pyproject.toml" ]]; then
        v="$(grep -E '^\s*version\s*=\s*"[0-9]' "$SOURCE_REPO/pyproject.toml" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
        [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && {
            echo "$v"
            return 0
        }
    fi
    if [[ -f "$SOURCE_REPO/VERSION" ]]; then
        v="$(tr -d '[:space:]' < "$SOURCE_REPO/VERSION")"
        [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && {
            echo "$v"
            return 0
        }
    fi
    echo "0.0.1"
}

increment_patch() {
    local version="${1#v}"
    local major minor patch
    IFS=. read -r major minor patch <<< "$version"
    echo "${major}.${minor}.$((patch + 1))"
}

highest_tag_version() {
    local tag=""
    cd "$SOURCE_REPO"
    tag="$(git tag -l 'v[0-9]*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)"
    if [[ -z "$tag" ]]; then
        return 1
    fi
    echo "${tag#v}"
}

cd "$SOURCE_REPO"

if LAST_VERSION="$(highest_tag_version)"; then
    VERSION="$(increment_patch "$LAST_VERSION")"
    VERSION_SOURCE="git tag v${LAST_VERSION} + 1 patch"
else
    VERSION="$(read_base_version)"
    VERSION_SOURCE="base version (no release tags yet)"
fi

if [[ "$VERBOSE" -eq 1 ]]; then
    echo "Version source: ${VERSION_SOURCE}"
    if [[ -n "${LAST_VERSION:-}" ]]; then
        echo "Last release tag: v${LAST_VERSION}"
    else
        echo "Last release tag: (none)"
    fi
    echo "Next version: ${VERSION}"
else
    echo "$VERSION"
fi
