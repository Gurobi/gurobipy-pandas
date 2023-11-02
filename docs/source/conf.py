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
    "nbsphinx",
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.code",
    "sphinx_toolbox.collapse",
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
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
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

# -- numpydoc magic linking

numpydoc_xref_param_type = True
numpydoc_xref_aliases = {
    "DataFrame": "pandas.DataFrame",
    "Series": "pandas.Series",
    "Index": "pandas.Index",
}
numpydoc_xref_ignore = {"optional", "or", "of"}
numpydoc_class_members_toctree = False

# -- Options for EPUB output

epub_show_urls = "footnote"
