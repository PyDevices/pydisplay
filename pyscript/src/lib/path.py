"""
path.py
To run this command when you launch *Python, type the following, substituting 'python' with the name
of your *Python executable, such as 'python3' or 'micropython':

    python -i lib/path.py

Or run an example in one shot:

    python -c "import lib.path; import myexample"

On microcontrollers, you may include it in your boot.py, main.py or code.py, whichever is appropriate:

    import lib.path

Edit the 'directories' tuple to include the directories you want to add to the path.
Only directories that already exist in the current working directory will be added to the path.
"""

# Edit this list to include the directories you want to add to the path.
directories = ["lib", "add_ons", "examples"]
prepend_directories = []

# Set to True to use relative paths instead of absolute paths.
RELPATH = True


def update():
    import os
    import sys

    def find_dir(directory):
        try:
            os.stat(directory)
            return True
        except OSError:
            return False

    def resolve_entry(directory):
        is_abs = directory.startswith("/") or (len(directory) > 1 and directory[1] == ":")
        target = directory if is_abs else cwd + directory
        if not find_dir(target):
            return None
        return target if is_abs or not RELPATH else directory

    cwd = os.getcwd()
    if cwd[-1] != "/":
        cwd += "/"

    prepended = []
    for directory in prepend_directories:
        entry = resolve_entry(directory)
        if entry is not None and entry not in sys.path:
            sys.path.insert(0, entry)
            prepended.append(entry)

    added = []
    for directory in directories:
        entry = resolve_entry(directory)
        if entry is not None and entry not in sys.path:
            sys.path.append(entry)
            added.append(entry)

    if prepended:
        print(f"path.py:  Prepended {prepended} to sys.path.")
    if added:
        print(f"path.py:  Added {added} to sys.path.")


def add(directory, first=False):
    """Register *directory* and call :func:`update`.

    With ``first=True``, the directory is inserted at the front of ``sys.path``
    so game-local modules (e.g. ``board_config.py``) shadow ``lib/`` defaults.
    """
    if first:
        prepend_directories.append(directory)
    else:
        directories.append(directory)
    update()


update()
