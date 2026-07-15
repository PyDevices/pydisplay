#!/usr/bin/env bash
# Create and push a release tag for this repo. Same interface in every PyDevices repo.
#
# Version is the optional VERSION argument, else auto-computed by
# next_release_version.sh (highest vX.Y.Z tag + 1 patch). Pushing the tag
# triggers this repo's publish workflow.
#
# Usage:
#   ./scripts/publish_release_tag.sh                # auto version; create tag
#   ./scripts/publish_release_tag.sh --push         # auto version; create + push
#   ./scripts/publish_release_tag.sh 0.0.5 --push   # explicit version; create + push
#   ./scripts/publish_release_tag.sh --dry-run      # preview only
#
# Preview the next version:  ./scripts/next_release_version.sh --verbose

set -euo pipefail

DO_PUSH=0
DRY_RUN=0
VERSION=""

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_release_tag.sh [VERSION] [--push] [--dry-run]

Create an annotated git tag vVERSION on the current commit.

  VERSION     Optional semver X.Y.Z. When omitted, computed by
              scripts/next_release_version.sh (highest tag + 1 patch).
  --push      Push the tag to origin (triggers this repo's publish workflow)
  --dry-run   Print the version that would be tagged; do not create a tag

Examples:
  ./scripts/publish_release_tag.sh --push
  ./scripts/publish_release_tag.sh 0.0.5 --push
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            DO_PUSH=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

AUTO=0
if [[ -z "$VERSION" ]]; then
    AUTO=1
    VERSION="$("$SCRIPT_DIR/next_release_version.sh")"
fi

VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: expected semver X.Y.Z, got: $VERSION" >&2
    exit 1
fi

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

if [[ "$AUTO" -eq 1 ]]; then
    "$SCRIPT_DIR/next_release_version.sh" --verbose
else
    echo "Version: ${VERSION} (explicit)"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry run — would create tag $TAG on $(git rev-parse --short HEAD)"
    exit 0
fi

git tag -a "$TAG" -m "Release $VERSION"
echo "Created annotated tag $TAG on $(git rev-parse --short HEAD)"

if [[ "$DO_PUSH" -eq 1 ]]; then
    git push origin "$TAG"
    echo "Pushed $TAG — this repo's publish workflow should start shortly."
else
    echo "Push to publish: git push origin $TAG"
fi
