"""Portable, idempotent path configuration for PyDevices runtimes."""

import os
import sys

# Get user home directory portably without os.path
home = os.getenv("HOME") or os.getenv("USERPROFILE") or "~"
home = home.replace("\\", "/").rstrip("/")
user_lib = home + "/.micropython/lib"

targets = [
    "",
    ".frozen",
    "lib",
    "utils",
    user_lib,
]

# Only append /usr/lib/micropython on Unix/Linux systems
is_windows = os.sep == "\\" or (hasattr(sys, "platform") and sys.platform == "win32")
if not is_windows:
    targets.append("/usr/lib/micropython")


def _norm(path):
    if path in ("", ".frozen"):
        return path
    p = path.replace("\\", "/").rstrip("/")
    if is_windows:
        p = p.lower()
    return p


insert_idx = 0
for t in targets:
    norm_t = _norm(t)
    found = False
    for idx, p in enumerate(sys.path):
        if _norm(p) == norm_t:
            found = True
            insert_idx = max(insert_idx, idx + 1)
            break
    if not found:
        sys.path.insert(insert_idx, t)
        insert_idx += 1

print("path.py:  path updated")
