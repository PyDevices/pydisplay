#!/bin/python

import json
import os

# Define constants
package_ver = "0.0.1"
repo_url = "github:PyDevices/pydisplay/"
repo_dir = os.getcwd() + "/"
src_dir = "src/"
output_dir = repo_dir
packages_dir = "packages/"
toml_full_path = output_dir + "html/pyscript.toml"
master_package_name = "pydisplay-bundle"

# list of package directories, dependencies and extra files in that package
packages = [
    ["add_ons", [], []],
    ["examples", [], []],
    ["lib/displaysys", [], ["board_config.py", "path.py"]],
    ["lib/eventsys", [], []],
    ["lib/graphics", [], []],
    ["lib/multimer", [], []],
]

# Packages omitted from pydisplay-bundle.json (still get their own packages/*.json).
bundle_exclude = ["examples", "add_ons"]
# Packages omitted from html/pyscript.toml (PyScript mounts add_ons for local demos).
toml_exclude = ["examples"]

SKIP_DIR_NAMES = {"__pycache__", ".git", ".mypy_cache", ".ruff_cache"}
SKIP_FILE_SUFFIXES = {".pyc", ".pyo"}
# Local upstream checkouts (gitignored) — never list in mip manifests.
PACKAGE_SKIP_DIRS = {"add_ons": {"gui"}}

# Dest paths omitted from wokwi/pydisplay-bundle.json (derived from packages/pydisplay-bundle.json).
WOKWI_BUNDLE_EXCLUDE_DESTS = {
    "jupyter_notebook.ipynb",
    "lib/board_config.py",
    "lib/displaysys/fbdisplay.py",
    "lib/displaysys/jndisplay.py",
    "lib/displaysys/pgdisplay.py",
    "lib/displaysys/psdisplay.py",
    "lib/multimer/_ctypes.py",
    "lib/multimer/_ffi.py",
    "lib/multimer/_polling.py",
    "lib/multimer/_sdl2.py",
    "lib/multimer/_threading.py",
    "lib/multimer/_async.py",
}
WOKWI_BUNDLE_EXCLUDE_PREFIXES = ("lib/displaysys/sdldisplay/",)
# Dest paths added only to wokwi/pydisplay-bundle.json (not in pydisplay-bundle).
WOKWI_BUNDLE_EXTRA_DESTS = [
    "add_ons/touch_keypad.py",
]


def should_include_file(filename):
    return not any(filename.endswith(suffix) for suffix in SKIP_FILE_SUFFIXES)


def exclude_from_wokwi_bundle(dest):
    if dest in WOKWI_BUNDLE_EXCLUDE_DESTS:
        return True
    return any(dest.startswith(prefix) for prefix in WOKWI_BUNDLE_EXCLUDE_PREFIXES)


def wokwi_bundle_from_master(master):
    urls = [entry for entry in master["urls"] if not exclude_from_wokwi_bundle(entry[0])]
    for dest in WOKWI_BUNDLE_EXTRA_DESTS:
        urls.append([dest, repo_url + os.path.join(src_dir, dest)])
    return {"urls": urls, "version": master["version"]}


# Create the data structures
package_dicts = {}
master_package = {"urls": [], "version": package_ver}
master_toml = ["[files]"]
# Standalone files included in the bundle but not discovered by package walks.
extra_files_added_to_master = [os.path.join(src_dir, "jupyter_notebook.ipynb")]

# Iterate over the packages and create the package files
for package_path, deps, extra_files in packages:
    # Define the package variables
    package_name = package_path.split("/")[-1]
    full_path = os.path.join(repo_dir, src_dir, package_path)
    parent_path = os.path.join("/".join(full_path.split("/")[:-1]))
    if package_name == package_path:
        trim_path = full_path.split(package_name)[0]
        package_sub_dir = ""
    else:
        trim_path = full_path
        package_sub_dir = package_name + "/"
    # Add a dictionary for the package
    package_dicts[package_name] = {"urls": [], "deps": deps, "version": package_ver}

    # Iterate over the extra files in the package
    for extra_file in sorted(extra_files):
        # Add the extra file to the package
        full_file_path = os.path.join(full_path.split(package_name)[0], extra_file)
        src_file = repo_url + os.path.relpath(full_file_path, repo_dir)
        package_dicts[package_name]["urls"].append([extra_file, src_file])

        if package_name not in bundle_exclude:
            master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
            master_package["urls"].append([master_dest_file, src_file])

        if package_name not in toml_exclude:
            master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
            toml_dest_dir = "/" + "/".join(master_dest_file.split("/")[:-1]) + "/"
            if toml_dest_dir == "//":
                toml_dest_dir = "/"
            master_toml.append(
                f'"../{os.path.relpath(full_file_path, repo_dir)}" = "{toml_dest_dir}"'
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
            dest_file = package_sub_dir + os.path.relpath(full_file_path, full_path)
            src_file = repo_url + os.path.relpath(full_file_path, repo_dir)
            package_dicts[package_name]["urls"].append([dest_file, src_file])

            if package_name not in bundle_exclude:
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                master_package["urls"].append([master_dest_file, src_file])

            if package_name not in toml_exclude:
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                toml_dest_dir = "/".join(master_dest_file.split("/")[:-1])
                if toml_dest_dir == "//":
                    toml_dest_dir = "/"
                toml_src_file = src_dir + master_dest_file
                master_toml.append(f'"../{toml_src_file}" = "/{toml_dest_dir}/"')

    if package_name not in toml_exclude:
        master_toml.append("")

# Add standalone bundle files not discovered by package walks.
for rel_path in extra_files_added_to_master:
    src_file = repo_url + rel_path
    master_dest_file = os.path.relpath(rel_path, src_dir)
    master_package["urls"].append([master_dest_file, src_file])

    toml_dest_dir = "/" + "/".join(master_dest_file.split("/")[:-1]) + "/"
    if toml_dest_dir == "//":
        toml_dest_dir = "/"
    master_toml.append(f'"../{rel_path}" = "{toml_dest_dir}"')

# Add the master package to the package dictionaries
package_dicts[master_package_name] = master_package


# Write the package .json files
for package_name, contents in package_dicts.items():
    package_file = output_dir + packages_dir + package_name + ".json"
    with open(package_file, "w") as f:
        json.dump(contents, f, indent=2)

# Write the master toml file
with open(toml_full_path, "w") as f:
    for line in master_toml:
        f.write(line + "\n")

# Wokwi browser sim: slim copy of pydisplay-bundle (not a packages/ entry).
wokwi_bundle_path = os.path.join(output_dir, "wokwi", "pydisplay-bundle.json")
os.makedirs(os.path.dirname(wokwi_bundle_path), exist_ok=True)
with open(wokwi_bundle_path, "w") as f:
    json.dump(wokwi_bundle_from_master(master_package), f, indent=2)

print(f"{__file__.split('/')[-1]} finished\n")
