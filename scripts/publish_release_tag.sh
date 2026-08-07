#!/usr/bin/env bash
# Create and push a release tag for this repo. Same interface in every PyDevices repo.
#
# Version is the optional VERSION argument, else auto-computed by
# next_release_version.sh (highest vX.Y.Z tag + 1 patch). Pushing the tag
# triggers this repo's publish workflow.
#
# Before tagging, pre-bumps TestPyPI floors in requirements.txt for packages
# this tag publishes (multimer, eventsys, displaysys) and commits that change
# so the release commit already carries the new floors.
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

# Packages uploaded by this repo's tag publish (same VERSION).
FLOOR_PACKAGES=(multimer eventsys displaysys)

usage() {
    cat <<'EOF'
Usage: ./scripts/publish_release_tag.sh [VERSION] [--push] [--dry-run]

Create an annotated git tag vVERSION on the current commit.

  VERSION     Optional semver X.Y.Z. When omitted, computed by
              scripts/next_release_version.sh (highest tag + 1 patch).
  --push      Push the branch (if floors committed) and tag to origin
  --dry-run   Print the version / floor bumps; do not commit or tag

Before tagging, bumps requirements.txt floors for multimer/eventsys/displaysys
to VERSION and commits when that file changes.

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

# Dirty tree only matters for real tag/commit; allow --dry-run on WIP branches.
if [[ "$DRY_RUN" -eq 0 ]]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Error: working tree has uncommitted changes; commit or stash before tagging." >&2
        exit 1
    fi
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

SET_ARGS=()
for pkg in "${FLOOR_PACKAGES[@]}"; do
    SET_ARGS+=("${pkg}=${VERSION}")
done
echo "Pre-bump requirements floors: ${SET_ARGS[*]}"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry run — would bump floors, commit if needed, then create tag $TAG on that commit"
    exit 0
fi

python3 "$SCRIPT_DIR/refresh-requirements.py" --set "${SET_ARGS[@]}"

if ! git diff --quiet -- requirements.txt; then
    git add requirements.txt
    git commit -m "$(cat <<EOF
Bump TestPyPI floors for v${VERSION} release.

EOF
)"
    echo "Committed requirements.txt floor bump for $TAG"
else
    echo "requirements.txt floors already at $VERSION; no floor commit"
fi

git tag -a "$TAG" -m "Release $VERSION"
echo "Created annotated tag $TAG on $(git rev-parse --short HEAD)"

if [[ "$DO_PUSH" -eq 1 ]]; then
    # Push the floor-bump commit (branch) before the tag so origin/main stays current.
    git push origin HEAD
    git push origin "$TAG"
    echo "Pushed HEAD and $TAG — this repo's publish workflow should start shortly."
else
    echo "Push to publish: git push origin HEAD && git push origin $TAG"
fi
