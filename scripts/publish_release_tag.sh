#!/usr/bin/env bash
# Create and push a semver release tag. Pushing vX.Y.Z triggers publish-micropython-lib
# (sync micropython-lib, MIP index, and TestPyPI upload).
#
# Usage:
#   ./scripts/publish_release_tag.sh 0.0.5
#   ./scripts/publish_release_tag.sh 0.0.5 --push

set -euo pipefail

DO_PUSH=0

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_release_tag.sh VERSION [--push]

Create an annotated git tag vVERSION on the current commit.

  --push    Push the tag to origin (triggers the publish workflow)

Without --push, prints the git push command to run manually.

Examples:
  ./scripts/publish_release_tag.sh 0.0.5 --push
  git push origin v0.0.5
EOF
}

VERSION=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            DO_PUSH=1
            shift
            ;;
        --help | -h)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -n "$VERSION" ]]; then
                echo "Unexpected argument: $1" >&2
                usage >&2
                exit 1
            fi
            VERSION=$1
            shift
            ;;
    esac
done

if [[ -z "$VERSION" ]]; then
    usage >&2
    exit 1
fi

VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: expected semver X.Y.Z, got: $VERSION" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
TAG="v$VERSION"

cd "$SOURCE_REPO"

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: working tree has uncommitted changes; commit or stash before tagging." >&2
    exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: tag $TAG already exists ($(git rev-parse --short "$TAG^{commit}"))" >&2
    exit 1
fi

git tag -a "$TAG" -m "Release $VERSION"
echo "Created annotated tag $TAG on $(git rev-parse --short HEAD)"

if [[ "$DO_PUSH" -eq 1 ]]; then
    git push origin "$TAG"
    echo "Pushed $TAG — publish-micropython-lib workflow should start shortly."
else
    echo "Push to publish: git push origin $TAG"
fi
