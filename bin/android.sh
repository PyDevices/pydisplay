#!/usr/bin/env bash
# Compatibility shim — android.sh lives in pydisplay_android/scripts/.
# Prefer: android.sh on PATH (~/bin → that script), or call the path below.
set -euo pipefail
_here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
_target="$(cd "$_here/../../pydisplay_android/scripts" && pwd)/android.sh"
if [[ ! -x "$_target" ]]; then
  echo "android.sh: moved to pydisplay_android/scripts/android.sh (not found at $_target)" >&2
  exit 1
fi
exec "$_target" "$@"
