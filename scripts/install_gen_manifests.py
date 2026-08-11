#!/bin/python

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

_scripts = Path(__file__).resolve().parent
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
from personal_examples import PERSONAL_EXAMPLE_DIRS  # noqa: E402

parser = argparse.ArgumentParser(description="Generate install and PyScript manifests.")
parser.add_argument(
    "--toml",
    action="store_true",
    help="also generate legacy micropython.toml and pyodide.toml configs",
)
args = parser.parse_args()

# Define constants
package_ver = "0.0.1"
repo_url = "github:PyDevices/pydisplay/"
repo_dir = os.getcwd() + "/"
src_dir = "src/"
output_dir = repo_dir
packages_dir = "packages/"
toml_full_path = output_dir + "web/pyscript/micropython.toml"
pyodide_toml_path = output_dir + "web/pyscript/pyodide.toml"
micropython_json_path = output_dir + "web/pyscript/micropython.json"
pyodide_json_path = output_dir + "web/pyscript/pyodide.json"
pydisplay_json_path = output_dir + "web/pyscript/pydisplay.json"
peterhinch_config_paths = {
    "nano": output_dir + "web/pyscript/peterhinch-nano.json",
    "micro": output_dir + "web/pyscript/peterhinch-micro.json",
    "touch": output_dir + "web/pyscript/peterhinch-touch.json",
}
peterhinch_packages = {
    "nano": "micropython-nano-gui",
    "micro": "micropython-micro-gui",
    "touch": "micropython-touch",
}

# list of package directories, dependencies and extra files in that package.
# eventsys installs from the micropython-lib MIP index — do not emit
# packages/eventsys.json. It still appears here so PyScript mounts stay generated.
# displaydev / multimer / events / keys / portable utils (byteswap, mip, …)
# live in micropython-hardware and are installed via mip or pip
# (gallery: desktop board_config deps; PyScript mounts via toml_only_mounts).
# Sister packages (pygraphics, usdl2, palettes, pdwidgets, lvgl) are not from
# this repo: frozen in firmware, or TestPyPI / MIP when needed (see url_maker.py).
packages = [
    [
        "utils",
        [["github:PyDevices/micropython-hardware/packages/utils.json", "main"]],
        [],
    ],
    ["examples", [], []],
    ["lib/eventsys", [], []],
]

# Emit packages/*.json only for GitHub-MIP / PyScript demo bundles.
# These names stay in `packages` for toml mounts but must not get a JSON file.
MIP_INDEX_ONLY = frozenset({"eventsys"})

# Packages omitted from web/pyscript/micropython.toml (PyScript mounts utils for browser examples).
toml_exclude = ["examples"]

# PyScript [files] mounts that are not part of any mip package JSON.
# These modules live in micropython-hardware/utils. Local serve.py and
# deploy-pyscript.yml map the URLs onto that tree so Pyodide can import mip
# before other installs, and so keypins/wifi/byteswap examples resolve.
toml_only_mounts: list[tuple[str, str]] = [
    ("src/utils/byteswap.py", "/utils/"),
    ("src/utils/frame_recorder.py", "/utils/"),
    ("src/utils/keypins.py", "/utils/"),
    ("src/utils/micropython.py", "/utils/"),
    ("src/utils/mip.py", "/utils/"),
    ("src/utils/viper_tools.py", "/utils/"),
    ("src/utils/wifi.py", "/utils/"),
]

SKIP_DIR_NAMES = {"__pycache__", ".git", ".mypy_cache", ".ruff_cache"}
# MicroPython mip only fetches .py / .mpy / .json (see micropython-lib mip).
MIP_FILE_SUFFIXES = {".py", ".mpy", ".json"}
# Local upstream checkouts (gitignored) — never list in mip manifests.
PACKAGE_SKIP_DIRS = {
    "utils": {"gui"},
    "examples": set(PERSONAL_EXAMPLE_DIRS),
}


def should_include_file(filename):
    """Keep only mip-safe source extensions (skip .bmp/.png/.sh/… uniformly)."""
    return Path(filename).suffix.lower() in MIP_FILE_SUFFIXES


def is_gitignored(path):
    """Skip generated/local-only files (e.g. graphics/framebuf.py from install_sync_framebuf)."""
    try:
        return (
            subprocess.run(
                ["git", "-C", repo_dir, "check-ignore", "-q", "--", path],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
    except OSError:
        return False


# Paths in micropython.toml / pyodide.toml [files] — relative to web/pyscript/ (browser URL ./src/...).
PYSCRIPT_TOML_SRC_PREFIX = "./"
# Local interpreters under vendor/; PyScript config key replaces the CDN build.
PYSCRIPT_INTERPRETER = "./vendor/micropython/micropython.mjs"
PYODIDE_INTERPRETER = "./vendor/pyodide/pyodide.mjs"


def pyscript_toml_file_entry(repo_relative_path: str, mount: str) -> str:
    """repo_relative_path e.g. src/utils/path.py; mount e.g. /utils/."""
    return f'"{PYSCRIPT_TOML_SRC_PREFIX}{repo_relative_path}" = "{mount}"'


package_dicts = {}
master_files = {}
master_toml = [
    f'interpreter = "{PYSCRIPT_INTERPRETER}"',
    "",
    "[files]",
]


def add_pyscript_file(repo_relative_path: str, mount: str) -> None:
    """Add one local source to both TOML and JSON-compatible file maps."""
    # board_config is now delivered via board_configs/* packages, not web mounts.
    if repo_relative_path.replace("\\", "/").endswith("/board_config.py"):
        return
    source = PYSCRIPT_TOML_SRC_PREFIX + repo_relative_path
    master_files[source] = mount
    master_toml.append(pyscript_toml_file_entry(repo_relative_path, mount))


for rel_path, mount in toml_only_mounts:
    add_pyscript_file(rel_path, mount)
master_toml.append("")

# Iterate over the packages and create the package files
for package_path, deps, extra_files in packages:
    # Define the package variables
    package_name = package_path.split("/")[-1]
    full_path = os.path.join(repo_dir, src_dir, package_path)
    package_sub_dir = "" if package_name == package_path else package_name + "/"
    # Add a dictionary for the package
    package_dicts[package_name] = {"urls": [], "deps": deps, "version": package_ver}

    # Iterate over the extra files in the package
    for extra_file in sorted(extra_files):
        # Add the extra file to the package
        full_file_path = os.path.join(full_path.split(package_name)[0], extra_file)
        src_file = repo_url + os.path.relpath(full_file_path, repo_dir)
        package_dicts[package_name]["urls"].append([extra_file, src_file])

        if package_name not in toml_exclude:
            master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
            toml_dest_dir = "/" + "/".join(master_dest_file.split("/")[:-1]) + "/"
            if toml_dest_dir == "//":
                toml_dest_dir = "/"
            add_pyscript_file(
                os.path.relpath(full_file_path, repo_dir).replace("\\", "/"),
                toml_dest_dir,
            )

    package_skip = PACKAGE_SKIP_DIRS.get(package_name, set())

    # Iterate over the directories in the package
    for root, dirs, files in os.walk(full_path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIR_NAMES and d not in package_skip)
        # Iterate over the sorted files list
        for f in sorted(files):
            if not should_include_file(f):
                continue
            # Add the file to the package
            full_file_path = os.path.join(root, f)
            if is_gitignored(full_file_path):
                continue
            dest_file = package_sub_dir + os.path.relpath(full_file_path, full_path)
            src_file = repo_url + os.path.relpath(full_file_path, repo_dir)
            package_dicts[package_name]["urls"].append([dest_file, src_file])

            if package_name not in toml_exclude:
                # Gallery loaders use ``import ps_loader``; mounted at VFS root below.
                # PyScript rejects the same source key twice in ``[files]``.
                if package_name == "utils" and f == "ps_loader.py":
                    continue
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                toml_dest_dir = "/".join(master_dest_file.split("/")[:-1])
                if toml_dest_dir == "//":
                    toml_dest_dir = "/"
                toml_src_file = src_dir + master_dest_file
                add_pyscript_file(toml_src_file, f"/{toml_dest_dir}/")

    if package_name not in toml_exclude:
        master_toml.append("")

# Write the package .json files (GitHub MIP only — not micropython-lib cores).
manual_package_stems = {
    "micropython-micro-gui",
    "micropython-nano-gui",
    "micropython-touch",
}
reserved_package_names = set(package_dicts) | manual_package_stems | set(MIP_INDEX_ONLY)
for package_name, contents in package_dicts.items():
    package_file = output_dir + packages_dir + package_name + ".json"
    if package_name in MIP_INDEX_ONLY:
        if os.path.isfile(package_file):
            os.remove(package_file)
            print(f"removed packages/{package_name}.json (use micropython-lib MIP index)")
        continue
    with open(package_file, "w") as f:
        json.dump(contents, f, indent=2)

# One MIP manifest per examples/<subdir>/ (for PyScript ?manifests= and GitHub mip).
# Package JSON lives in packages/<name>.json and is served via web/pyscript/packages
# (symlink → ../../packages). MicroPython mip resolves *file* URLs in the package
# against the loader page base (…/web/pyscript/), not against packages/<name>.json —
# same as the old web/pyscript/<name>.json layouts: use ./src/examples/….
# Only .py/.mpy/.json are listed (mip cannot install binary assets).
examples_root = os.path.join(repo_dir, src_dir, "examples")
example_package_names = []
for entry in sorted(os.listdir(examples_root)):
    example_dir = os.path.join(examples_root, entry)
    if not os.path.isdir(example_dir):
        continue
    if entry in SKIP_DIR_NAMES or entry in PERSONAL_EXAMPLE_DIRS:
        continue
    if entry in reserved_package_names:
        print(f"skip examples/{entry}: name conflicts with packages/{entry}.json")
        continue
    urls = []
    for root, dirs, files in os.walk(example_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIR_NAMES)
        for f in sorted(files):
            if not should_include_file(f):
                continue
            full_file_path = os.path.join(root, f)
            if is_gitignored(full_file_path):
                continue
            rel_from_examples = os.path.relpath(full_file_path, examples_root).replace("\\", "/")
            # Loader page base is web/pyscript/ (see mip resolution); packages/ is only
            # where the manifest JSON is fetched from (via the symlink).
            src_file = "./src/examples/" + rel_from_examples
            urls.append([rel_from_examples, src_file])
    package_file = output_dir + packages_dir + entry + ".json"
    if not urls:
        # Drop a prior manifest that was only binary assets (e.g. assets/).
        if os.path.isfile(package_file) and entry not in reserved_package_names:
            os.remove(package_file)
            print(f"removed packages/{entry}.json (no mip-safe files)")
        continue
    with open(package_file, "w") as f:
        json.dump({"urls": urls, "version": package_ver}, f, indent=2)
    example_package_names.append(entry)

# Gallery loaders use `import ps_loader` (top-level); also mount at VFS root.
add_pyscript_file("src/utils/ps_loader.py", "/")

# web/pyscript/packages → ../../packages (same layout as web/pyscript/src).
pyscript_packages_link = os.path.join(output_dir, "web", "pyscript", "packages")
packages_abs = os.path.join(output_dir, packages_dir.rstrip("/"))
if os.path.islink(pyscript_packages_link) or os.path.exists(pyscript_packages_link):
    if not os.path.islink(pyscript_packages_link):
        raise SystemExit(f"{pyscript_packages_link} exists and is not a symlink")
    if os.readlink(pyscript_packages_link) not in ("../../packages", packages_abs):
        os.remove(pyscript_packages_link)
        os.symlink("../../packages", pyscript_packages_link)
else:
    os.symlink("../../packages", pyscript_packages_link)

# Legacy TOML output is opt-in. JSON composition is the default browser path.
if args.toml:
    with open(toml_full_path, "w") as f:
        for line in master_toml:
            f.write(line + "\n")

    with open(pyodide_toml_path, "w") as f:
        for line in master_toml:
            if line.startswith("interpreter ="):
                f.write(f'interpreter = "{PYODIDE_INTERPRETER}"\n')
            else:
                f.write(line + "\n")


def github_mip_raw_url(source: str) -> str:
    """Convert github:owner/repo/path to its raw GitHub source URL."""
    prefix = "github:"
    if not source.startswith(prefix):
        raise ValueError(f"Unsupported Peter Hinch manifest URL: {source}")
    owner, repository, path = source[len(prefix) :].split("/", 2)
    return f"https://raw.githubusercontent.com/{owner}/{repository}/master/{path}"


# JSON configs keep runtimes separate from the shared pydisplay filesystem so a
# page can compose the runtime it needs before PyScript starts.
with open(micropython_json_path, "w") as f:
    json.dump({"interpreter": PYSCRIPT_INTERPRETER}, f, indent=2)
    f.write("\n")
with open(pyodide_json_path, "w") as f:
    json.dump({"interpreter": PYODIDE_INTERPRETER}, f, indent=2)
    f.write("\n")
with open(pydisplay_json_path, "w") as f:
    json.dump({"files": master_files}, f, indent=2)
    f.write("\n")

# The manual package manifests remain the source of truth for each upstream GUI
# file inventory.
for gui, package_stem in peterhinch_packages.items():
    package_path = output_dir + packages_dir + package_stem + ".json"
    with open(package_path) as f:
        gui_package = json.load(f)
    files = {}
    for destination, source in gui_package["urls"]:
        files[github_mip_raw_url(source)] = "/utils/" + destination
    with open(peterhinch_config_paths[gui], "w") as f:
        json.dump({"files": files}, f, indent=2)
        f.write("\n")

print(
    f"{__file__.split('/')[-1]} finished "
    f"({len(package_dicts)} lib packages, {len(example_package_names)} example packages)\n"
)
