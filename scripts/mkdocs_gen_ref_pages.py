"""Generate the code reference pages and navigation."""

from pathlib import Path
import sys

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = Path(__file__).parent.parent

# (source tree, output prefix under reference/, nav prefix, extra sys.path entries)
# pygraphics lives in the sibling PyDevices/pygraphics repo — not under src/lib.
SOURCE_TREES = (
    (
        root / "src/lib",
        Path("reference"),
        (),
        ("", "displaysys", "eventsys", "multimer"),
    ),
    (
        root / "src/utils",
        Path("reference", "utils"),
        ("utils",),
        ("",),
    ),
)

SKIP_DIR_NAMES = {"__pycache__", "fonts"}
# Gitignored upstream checkout — same omit as install_gen_manifests PACKAGE_SKIP_DIRS.
ADD_ONS_SKIP_DIR_NAMES = {"gui"}


def _should_skip(parts: tuple[str, ...]) -> bool:
    """Skip private modules/packages and non-documentable names."""
    if not parts:
        return True
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True
    if any(part.endswith(".bak") for part in parts):
        return True
    # Any underscore path segment is private (e.g. multimer/_backends/…).
    if any(part.startswith("_") for part in parts):
        return True
    return parts[-1] == "__main__"


for src, ref_prefix, nav_prefix, path_entries in SOURCE_TREES:
    if not src.is_dir():
        continue
    for entry in path_entries:
        sys.path.append(str(src / entry) if entry else str(src))

    for path in sorted(src.rglob("*.py")):
        rel_parts = path.relative_to(src).parts
        if any(p in SKIP_DIR_NAMES for p in rel_parts):
            continue
        if src == root / "src" / "utils" and any(p in ADD_ONS_SKIP_DIR_NAMES for p in rel_parts):
            continue

        module_path = path.relative_to(src).with_suffix("")
        doc_path = module_path.with_suffix(".md")
        full_doc_path = ref_prefix / doc_path

        parts = tuple(module_path.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")

        if _should_skip(parts):
            continue

        nav[nav_prefix + parts] = full_doc_path.relative_to("reference").as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"::: {ident}")

        mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
