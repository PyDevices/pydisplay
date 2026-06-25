"""Copy the LVGL Jupyter notebook into the docs site so mkdocs-jupyter can render it.

The notebook is maintained at ``src/jupyter_notebook.ipynb`` (next to the source it
imports, so it can be executed locally). MkDocs only renders files under ``docs_dir``,
so this generator copies it into the virtual docs tree at build time. Outputs are
stripped from the committed notebook (nbstripout), so the rendered page shows the
markdown and code cells only -- it is not executed during the build.
"""

from pathlib import Path

import mkdocs_gen_files

ROOT = Path(__file__).parent.parent

# (source notebook relative to repo root, destination path under docs_dir)
NOTEBOOKS = (("src/jupyter_notebook.ipynb", "platforms/jupyter-notebook.ipynb"),)

for source_rel, docs_path in NOTEBOOKS:
    source = ROOT / source_rel
    if not source.is_file():
        continue
    with mkdocs_gen_files.open(docs_path, "w") as fd:
        fd.write(source.read_text(encoding="utf-8"))
    mkdocs_gen_files.set_edit_path(docs_path, source.relative_to(ROOT))
