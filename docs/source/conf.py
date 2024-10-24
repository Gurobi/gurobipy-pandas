# Configuration file for the Sphinx documentation builder.

import os

import gurobipy_pandas

# -- Project information -----------------------------------------------------


project = "gurobipy-pandas"
author = "Gurobi Optimization, LLC"
copyright = "Gurobi Optimization, LLC"
html_title = "gurobipy-pandas documentation"

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

docutils_tab_width = 4
nbsphinx_custom_formats = {
    ".md": ["jupytext.reads", {"fmt": "myst"}],
}

html_theme = "gurobi_sphinxtheme"
html_favicon = "https://www.gurobi.com/favicon.ico"
html_show_sphinx = False

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

# -- Note pointing to notebook downloads

nbsphinx_prolog = """

.. note::

   This is example is available as a Jupyter notebook. Download it and all
   necessary data files :download:`here </artifact/gurobipy-pandas-examples.zip>`.

"""

# Customisation for Furo/gurobi-sphinxtheme

html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/scroll-end.html",
    ],
}

# Customisation for readthedocs

if os.environ.get("READTHEDOCS", "") == "True":
    # Date needed by Furo theme to enable icons/links/etc
    html_context = {
        "READTHEDOCS": True,
        "github_user": "Gurobi",
        "github_repo": "gurobipy-pandas",
        "github_version": "main",
        "display_github": True,
        "conf_py_path": "/docs/source/",
    }

    # Set the canonical URL to point to the stable version docs
    rtd_version = os.environ.get("READTHEDOCS_VERSION")
    rtd_url = os.environ.get("READTHEDOCS_CANONICAL_URL")
    html_baseurl = rtd_url.replace(rtd_version, "stable")
