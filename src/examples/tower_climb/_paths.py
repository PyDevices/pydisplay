"""Package paths for a self-contained tower_climb example tree."""

import os

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PKG_DIR, "assets")
TOOLS_DIR = os.path.join(PKG_DIR, "tools")
TRACE_DIR = os.path.join(PKG_DIR, "trace")
SRC_DIR = os.path.dirname(os.path.dirname(PKG_DIR))
REPO_ROOT = os.path.dirname(SRC_DIR)
GAME_SCRIPT = os.path.join(PKG_DIR, "tower_climb.py")


def asset_path(name):
    return os.path.join(ASSETS_DIR, name)
