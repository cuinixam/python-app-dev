# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
from pathlib import Path

import mlx.traceability

project_root_path = Path(__file__).parent.parent

for path in ["src", "tests"]:
    sys.path.insert(0, project_root_path.joinpath(path).as_posix())


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Python App Development"
copyright = "2023, cuinixam"
author = "cuinixam"
release = "0.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

# markdown to rst (m2r) config - @see https://pypi.org/project/m2r/
extensions.append("m2r")

# TODO: enable this extension when is is supported by readthedocs
# draw.io config - @see https://pypi.org/project/sphinxcontrib-drawio/
# extensions.append("sphinxcontrib.drawio")
# drawio_default_transparency = True

# mermaid config - @see https://pypi.org/project/sphinxcontrib-mermaid/
extensions.append("sphinxcontrib.mermaid")

# Configure extensions for include doc-strings from code
extensions.extend(
    [
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.napoleon",
        "sphinx.ext.viewcode",
    ]
)

# The bibtex extension allows BibTeX citations to be inserted into documentation
# https://pypi.org/project/sphinxcontrib-bibtex/
extensions.append("sphinxcontrib.bibtex")
bibtex_bibfiles = ["refs.bib"]

# mlx.traceability config - https://pypi.org/project/mlx-traceability/
extensions.append("mlx.traceability")
html_static_path = [os.path.join(os.path.dirname(mlx.traceability.__file__), "assets")]
# Make relationship like 'validated_by' be shown for each requirement
traceability_render_relationship_per_item = True

# The suffix of source filenames.
source_suffix = [
    ".rst",
    ".md",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Resize rtd theme
extensions.append("sphinx_rtd_size")
sphinx_rtd_size_width = "90%"

# copy button for code block
extensions.append("sphinx_copybutton")

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
