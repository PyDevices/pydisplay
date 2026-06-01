#!/bin/python

import os
import json


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
    ["lib/palettes", [], []],
]

master_exclude = ["examples"]


# Create the data structures
package_dicts = {}
master_package = {"urls": [], "version": package_ver}
master_toml = ["[files]"]
extra_files_added_to_master = ["jupyter_notebook.ipynb"]

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

        if package_name not in master_exclude:
            if full_file_path not in extra_files_added_to_master:
                # Add the file the master package
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                master_package["urls"].append([master_dest_file, src_file])

                # Add the file to the master toml
                toml_dest_dir = "/" + "/".join(master_dest_file.split("/")[:-1]) + "/"
                if toml_dest_dir == "//":
                    toml_dest_dir = "/"
                master_toml.append(
                    f'"../{os.path.relpath(full_file_path, repo_dir)}" = "{toml_dest_dir}"'
                )
                extra_files_added_to_master.append(full_file_path)

    # Iterate over the directories in the package
    for root, _, files in os.walk(full_path):
        # Iterate over the sorted files list
        for f in sorted(files):
            # Add the file to the package
            full_file_path = os.path.join(root, f)
            dest_file = package_sub_dir + os.path.relpath(full_file_path, full_path)
            src_file = repo_url + os.path.relpath(full_file_path, repo_dir)
            package_dicts[package_name]["urls"].append([dest_file, src_file])

            if package_name not in master_exclude:
                # Add the file to the master package
                master_dest_file = os.path.relpath(full_file_path, repo_dir + src_dir)
                master_package["urls"].append([master_dest_file, src_file])

                # Add the file to the master toml
                toml_dest_dir = "/".join(master_dest_file.split("/")[:-1])
                if toml_dest_dir == "//":
                    toml_dest_dir = "/"
                toml_src_file = src_dir + master_dest_file
                master_toml.append(f'"../{toml_src_file}" = "/{toml_dest_dir}/"')

    # Add a blank line to the master toml to make it easier to read
    if package_name not in master_exclude:
        master_toml.append("")

# add extra files to the master package and toml
for extra_file in extra_files_added_to_master:
    src_file = repo_url + src_dir + extra_file
    master_dest_file = os.path.relpath(extra_file, repo_dir)
    master_package["urls"].append([master_dest_file, src_file])

    toml_dest_dir = "/" + "/".join(master_dest_file.split("/")[:-1]) + "/"
    if toml_dest_dir == "//":
        toml_dest_dir = "/"
    toml_src_file = src_dir + master_dest_file
    master_toml.append(f'"../{toml_src_file}" = "{toml_dest_dir}"')

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

print(f"{__file__.split('/')[-1]} finished\n")
