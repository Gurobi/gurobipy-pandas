# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

import gurobipy_pandas

project = "gurobipy-pandas"
copyright = "2022, Gurobi Optimization"
author = "Gurobi Optimization"

version = gurobipy_pandas.__version__
release = version

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.collapse",
    "sphinx_toolbox.code",
    "nbsphinx",
    "sphinx_copybutton",
]

pygments_style = "vs"
docutils_tab_width = 4
nbsphinx_custom_formats = {
    ".md": ["jupytext.reads", {"fmt": "myst"}],
}

html_theme = "sphinx_rtd_theme"

nbsphinx_kernel_name = "python3"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

autodoc_typehints = "none"

copybutton_prompt_text = ">>> "

extlinks_detect_hardcoded_links = True
extlinks = {
    "pypi": ("https://pypi.org/project/%s/", "%s"),
    "ghsrc": ("https://github.com/Gurobi/gurobipy-pandas/tree/main/%s", "%s"),
}

# -- Options for EPUB output

epub_show_urls = "footnote"
