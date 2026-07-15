#!/bin/python

import json
import os
from pathlib import Path
import subprocess
import sys

_scripts = Path(__file__).resolve().parent
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
from personal_examples import PERSONAL_EXAMPLE_DIRS  # noqa: E402

# Define constants
package_ver = "0.0.1"
repo_url = "github:PyDevices/pydisplay/"
repo_dir = os.getcwd() + "/"
src_dir = "src/"
output_dir = repo_dir
packages_dir = "packages/"
toml_full_path = output_dir + "web/pyscript/micropython.toml"
pyodide_toml_path = output_dir + "web/pyscript/pyodide.toml"

# list of package directories, dependencies and extra files in that package
packages = [
    ["add_ons", [], []],
    ["examples", [], []],
    ["lib/displaysys", [], ["board_config.py", "path.py"]],
    ["lib/eventsys", [], []],
    ["lib/graphics", [], []],
    ["lib/multimer", [], []],
]

# Packages omitted from web/pyscript/micropython.toml (PyScript mounts add_ons for browser examples).
toml_exclude = ["examples"]

SKIP_DIR_NAMES = {"__pycache__", ".git", ".mypy_cache", ".ruff_cache"}
SKIP_FILE_SUFFIXES = {".pyc", ".pyo"}
# Local upstream checkouts (gitignored) — never list in mip manifests.
PACKAGE_SKIP_DIRS = {
    "add_ons": {"gui"},
    "examples": set(PERSONAL_EXAMPLE_DIRS),
}


def should_include_file(filename):
    return not any(filename.endswith(suffix) for suffix in SKIP_FILE_SUFFIXES)


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
    """repo_relative_path e.g. src/lib/path.py; mount e.g. /lib/ or /lib/graphics/."""
    return f'"{PYSCRIPT_TOML_SRC_PREFIX}{repo_relative_path}" = "{mount}"'


package_dicts = {}
master_toml = [
    f'interpreter = "{PYSCRIPT_INTERPRETER}"',
    "",
    "[files]",
]

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
            master_toml.append(
                pyscript_toml_file_entry(
                    os.path.relpath(full_file_path, repo_dir).replace("\\", "/"),
                    toml_dest_dir,
                )
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
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                toml_dest_dir = "/".join(master_dest_file.split("/")[:-1])
                if toml_dest_dir == "//":
                    toml_dest_dir = "/"
                toml_src_file = src_dir + master_dest_file
                master_toml.append(pyscript_toml_file_entry(toml_src_file, f"/{toml_dest_dir}/"))

    if package_name not in toml_exclude:
        master_toml.append("")

# Write the package .json files
for package_name, contents in package_dicts.items():
    package_file = output_dir + packages_dir + package_name + ".json"
    with open(package_file, "w") as f:
        json.dump(contents, f, indent=2)

# Write the master toml files (same [files]; MicroPython vs Pyodide interpreter).
with open(toml_full_path, "w") as f:
    for line in master_toml:
        f.write(line + "\n")

with open(pyodide_toml_path, "w") as f:
    for line in master_toml:
        if line.startswith("interpreter ="):
            f.write(f'interpreter = "{PYODIDE_INTERPRETER}"\n')
        else:
            f.write(line + "\n")

print(f"{__file__.split('/')[-1]} finished\n")
