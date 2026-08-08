#!/usr/bin/env bash
# Stage a host .py (cwd path) onto the PyDevices Android launcher via adb and
# relaunch. Resolves like CLI python/micropython — NOT like pyscript.sh gallery.
#
# Usage (from e.g. pydisplay/src):
#   ../bin/android.sh examples/lv_test_timer.py
#   ../bin/android.sh examples/paint.py --kit
#   ../bin/android.sh -m lv_test_timer          # relaunch existing staged/on-device name
#   ../bin/android.sh --clear
#   ../bin/android.sh --logcat
#
# Environment:
#   ADB                   Override adb executable
#   ANDROID_SERIAL        Device serial (-s for adb.exe)
#   PACKAGE_ID            Default org.pydevices.launcher
#   ACTIVITY              Default org.kivy.android.PythonActivity
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PYDISPLAY_ROOT="${PYDISPLAY_ROOT:-$(cd "$_SCRIPT_DIR/.." && pwd)}"

PACKAGE_ID="${PACKAGE_ID:-org.pydevices.launcher}"
ACTIVITY="${ACTIVITY:-org.kivy.android.PythonActivity}"
COMPONENT="${PACKAGE_ID}/${ACTIVITY}"

FILE_ARG=""
MODULE_ARG=""
CLEAR=0
LOGCAT=0
KIT=0
HOLD_S=""
DEPS_ARG=""
MODULES_ARG=""
MANIFESTS_ARG=""

usage() {
  cat <<EOF
Usage: ./bin/android.sh [<opts>] [<file> | -m <module>]
       ./bin/android.sh --clear
       ./bin/android.sh --logcat

Stage a Python file from the caller's cwd onto org.pydevices.launcher (adb)
and relaunch. Path resolution matches CLI python — not pyscript gallery lookup.

  <file>            path relative to \$PWD (or absolute); must exist
  -m <module>       set run_entry to <module> and relaunch (no host file push)
  --clear           remove run/ + run_entry (+ run_argv); back to LVGL home
  --logcat          follow python/SDL logcat after start (or alone)
  --kit             write run_argv with "kit" for example_test_kit / lv_test_timer
  --hold-s SEC      after the entry returns, keep presenting for SEC (oneshot hold)
  --deps A,B        optional companion staging (host packages/ or names)
  --modules A,B     optional: push src/examples/<name>.py beside entry when found
  --manifests A,B   optional: push packages/<name>.json when found under repo

Environment:
  ADB  ANDROID_SERIAL  PACKAGE_ID  ACTIVITY  PYDISPLAY_ROOT
EOF
}

is_wsl() {
  if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    return 0
  fi
  if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
    return 0
  fi
  return 1
}

pick_adb() {
  if [[ -n "${ADB:-}" ]]; then
    echo "$ADB"
    return 0
  fi
  if is_wsl && command -v adb.exe >/dev/null 2>&1; then
    echo "adb.exe"
    return 0
  fi
  local candidates=(
    "${ANDROID_HOME:-}/platform-tools/adb"
    "${ANDROID_SDK_ROOT:-}/platform-tools/adb"
    "$HOME/Android/Sdk/platform-tools/adb"
    "$HOME/.buildozer/android/platform/android-sdk/platform-tools/adb"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  if command -v adb >/dev/null 2>&1; then
    echo "adb"
    return 0
  fi
  return 1
}

adb_cmd() {
  if [[ -n "${ANDROID_SERIAL:-}" ]]; then
    "$ADB_BIN" -s "$ANDROID_SERIAL" "$@"
  else
    "$ADB_BIN" "$@"
  fi
}

list_devices() {
  adb_cmd devices | tr -d '\r' | awk 'NR>1 && $2=="device" { print $1 }'
}

require_device() {
  mapfile -t DEVICES < <(list_devices)
  if [[ ${#DEVICES[@]} -eq 0 ]]; then
    echo "android.sh: no adb device connected" >&2
    echo "  Start an emulator (or plug in a phone), then re-run." >&2
    exit 1
  fi
  if [[ -z "${ANDROID_SERIAL:-}" && ${#DEVICES[@]} -gt 1 ]]; then
    export ANDROID_SERIAL="${DEVICES[0]}"
    echo "android.sh: multiple devices; using $ANDROID_SERIAL" >&2
  elif [[ -z "${ANDROID_SERIAL:-}" ]]; then
    export ANDROID_SERIAL="${DEVICES[0]}"
  fi
}

require_package() {
  if ! adb_cmd shell pm path "$PACKAGE_ID" 2>/dev/null | tr -d '\r' | grep -q .; then
    echo "android.sh: package not installed: $PACKAGE_ID" >&2
    echo "  Build/install: cd ../pydisplay_android && ./build_android.sh -y && ./scripts/emulator.sh" >&2
    exit 1
  fi
}

run_as() {
  adb_cmd shell "run-as $PACKAGE_ID sh -c $(printf '%q' "$*")"
}

# Push host file to /data/local/tmp then copy into app files (direct push often fails).
stage_file() {
  local host_path=$1
  local dest_rel=$2
  local base
  base="$(basename "$host_path")"
  local tmp="/data/local/tmp/pydisplay-android-$base"
  adb_cmd push "$host_path" "$tmp" >/dev/null
  adb_cmd shell "run-as $PACKAGE_ID sh -c 'mkdir -p files/app/$(dirname "$dest_rel"); cp $tmp files/app/$dest_rel'"
}

write_app_file() {
  local dest_rel=$1
  local content=$2
  local tmp
  tmp="$(mktemp)"
  printf '%s\n' "$content" >"$tmp"
  stage_file "$tmp" "$dest_rel"
  rm -f "$tmp"
}

relaunch() {
  adb_cmd shell am force-stop "$PACKAGE_ID" >/dev/null || true
  adb_cmd shell am start -n "$COMPONENT" >/dev/null
  echo "android.sh: launched $COMPONENT"
}

do_clear() {
  adb_cmd shell "run-as $PACKAGE_ID sh -c 'rm -rf files/app/run files/app/run_entry files/app/run_argv'"
  echo "android.sh: cleared staged run/; relaunching launcher home"
  relaunch
}

do_logcat() {
  adb_cmd logcat -c || true
  exec adb_cmd logcat -v time python:V SDL:V AndroidRuntime:E '*:S'
}

stage_optional_csv() {
  local kind=$1
  local csv=$2
  [[ -n "$csv" ]] || return 0
  local IFS=','
  local name
  for name in $csv; do
    name="$(echo "$name" | tr -d '[:space:]')"
    [[ -n "$name" ]] || continue
    case "$kind" in
      modules)
        if [[ -f "$PYDISPLAY_ROOT/src/examples/${name}.py" ]]; then
          stage_file "$PYDISPLAY_ROOT/src/examples/${name}.py" "run/${name}.py"
          echo "android.sh: staged module $name"
        else
          echo "android.sh: warning: module not found: $name" >&2
        fi
        ;;
      manifests)
        if [[ -f "$PYDISPLAY_ROOT/packages/${name}.json" ]]; then
          stage_file "$PYDISPLAY_ROOT/packages/${name}.json" "run/${name}.json"
          echo "android.sh: staged manifest $name"
        else
          echo "android.sh: warning: manifest not found: $name" >&2
        fi
        ;;
      deps)
        # Dep names are for documentation / future on-device pip; core stack is baked.
        echo "android.sh: note: --deps $name (baked APK should already provide it)" >&2
        ;;
    esac
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --clear)
      CLEAR=1
      shift
      ;;
    --logcat)
      LOGCAT=1
      shift
      ;;
    --kit)
      KIT=1
      shift
      ;;
    --hold-s)
      HOLD_S="${2:?--hold-s requires seconds}"
      shift 2
      ;;
    -m)
      MODULE_ARG="${2:?-m requires a module name}"
      shift 2
      ;;
    --deps)
      DEPS_ARG="${2:?--deps requires a value}"
      shift 2
      ;;
    --modules)
      MODULES_ARG="${2:?--modules requires a value}"
      shift 2
      ;;
    --manifests)
      MANIFESTS_ARG="${2:?--manifests requires a value}"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "android.sh: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$FILE_ARG" ]]; then
        echo "android.sh: unexpected argument: $1" >&2
        exit 1
      fi
      FILE_ARG=$1
      shift
      ;;
  esac
done

ADB_BIN="$(pick_adb)" || {
  echo "android.sh: adb not found (on WSL install platform-tools and use adb.exe)" >&2
  exit 1
}
if is_wsl; then
  echo "android.sh: using adb: $ADB_BIN" >&2
fi

require_device
require_package

if [[ "$CLEAR" -eq 1 ]]; then
  do_clear
  if [[ "$LOGCAT" -eq 1 ]]; then
    do_logcat
  fi
  exit 0
fi

if [[ -z "$FILE_ARG" && -z "$MODULE_ARG" ]]; then
  if [[ "$LOGCAT" -eq 1 ]]; then
    do_logcat
  fi
  # Bare invoke: relaunch current entry (launcher or last staged).
  relaunch
  exit 0
fi

ENTRY_NAME=""

if [[ -n "$FILE_ARG" ]]; then
  if [[ "$FILE_ARG" = /* ]]; then
    RESOLVED="$FILE_ARG"
  else
    RESOLVED="$(pwd)/$FILE_ARG"
  fi
  if [[ ! -e "$RESOLVED" ]]; then
    echo "android.sh: file not found: $FILE_ARG (cwd=$(pwd))" >&2
    exit 1
  fi
  if [[ -d "$RESOLVED" ]]; then
    echo "android.sh: '$FILE_ARG' is a directory; pass a .py file or use -m" >&2
    exit 1
  fi
  STEM="$(basename "$RESOLVED")"
  STEM="${STEM%.py}"
  ENTRY_NAME="$STEM"
  adb_cmd shell "run-as $PACKAGE_ID sh -c 'rm -rf files/app/run; mkdir -p files/app/run'"
  stage_file "$RESOLVED" "run/${STEM}.py"
  echo "android.sh: staged $RESOLVED -> run/${STEM}.py"
  # Nested package examples only (e.g. examples/chango/chango.py) — never the
  # flat examples/*.py tree, which would push hundreds of unrelated siblings.
  ENTRY_DIR="$(dirname "$RESOLVED")"
  EXAMPLES_ROOT="$PYDISPLAY_ROOT/src/examples"
  if [[ -d "$ENTRY_DIR" && "$ENTRY_DIR" != "$EXAMPLES_ROOT" && "$ENTRY_DIR" == "$EXAMPLES_ROOT"/* ]]; then
    for sibling in "$ENTRY_DIR"/*.py; do
      [[ -f "$sibling" ]] || continue
      sib_base="$(basename "$sibling")"
      [[ "$sib_base" == "${STEM}.py" ]] && continue
      stage_file "$sibling" "run/${sib_base}"
      echo "android.sh: staged sibling ${sib_base}"
    done
  fi
  stage_optional_csv deps "$DEPS_ARG"
  stage_optional_csv modules "$MODULES_ARG"
  stage_optional_csv manifests "$MANIFESTS_ARG"
elif [[ -n "$MODULE_ARG" ]]; then
  ENTRY_NAME="$MODULE_ARG"
  # Allow -m examples.foo -> foo if dotted
  if [[ "$ENTRY_NAME" == examples.* ]]; then
    ENTRY_NAME="${ENTRY_NAME#examples.}"
  fi
fi

if [[ -n "$HOLD_S" ]]; then
  # Oneshot examples draw once and return; Android splash / Activity teardown
  # then hide the frame. Hold with periodic show()+event pump so pixels stay up.
  hold_tmp="$(mktemp)"
  cat >"$hold_tmp" <<EOF
import importlib
import time

importlib.import_module(${ENTRY_NAME@Q})
try:
    from board_config import display_drv
except Exception:
    display_drv = None
_deadline = time.time() + float(${HOLD_S@Q})
while time.time() < _deadline:
    if display_drv is not None:
        try:
            display_drv.show()
        except Exception:
            pass
    try:
        import usdl2

        _e = usdl2.SDL_Event()
        while usdl2.SDL_PollEvent(_e):
            pass
    except Exception:
        pass
    time.sleep(0.05)
EOF
  stage_file "$hold_tmp" "run/_android_hold.py"
  rm -f "$hold_tmp"
  ENTRY_NAME="_android_hold"
  echo "android.sh: hold ${HOLD_S}s after entry via _android_hold"
fi

write_app_file "run_entry" "$ENTRY_NAME"
if [[ "$KIT" -eq 1 ]]; then
  write_app_file "run_argv" "kit"
  # lv_test_timer kit imports quit_inject from tools/; stage beside the entry.
  if [[ -f "$PYDISPLAY_ROOT/tools/quit_inject.py" ]]; then
    stage_file "$PYDISPLAY_ROOT/tools/quit_inject.py" "run/quit_inject.py"
    echo "android.sh: staged quit_inject.py for kit mode"
  fi
else
  adb_cmd shell "run-as $PACKAGE_ID sh -c 'rm -f files/app/run_argv'" || true
fi

adb_cmd logcat -c || true
relaunch

if [[ "$LOGCAT" -eq 1 ]]; then
  do_logcat
fi
