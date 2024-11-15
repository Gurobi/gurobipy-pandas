# Configuration file for the Sphinx documentation builder.

import os

import gurobipy_pandas

project = "gurobipy-pandas"
author = "Gurobi Optimization, LLC"
copyright = "Gurobi Optimization, LLC"

version = gurobipy_pandas.__version__
release = version

html_title = f"gurobipy-pandas documentation v{release}"

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

# Add shorthand and keyword ignores for numpydoc
numpydoc_xref_param_type = True
numpydoc_xref_aliases = {
    "DataFrame": "pandas.DataFrame",
    "Series": "pandas.Series",
    "Index": "pandas.Index",
}
numpydoc_xref_ignore = {"optional", "or", "of"}
numpydoc_class_members_toctree = False

# Add a note pointing to notebook downloads in notebook headers
nbsphinx_prolog = """

.. note::

   This is example is available as a Jupyter notebook. Download it and all
   necessary data files :download:`here </artifact/gurobipy-pandas-examples.zip>`.

"""

if os.environ.get("READTHEDOCS", "") == "True":
    # Data needed by Furo theme to enable icons/links/etc
    html_context = {
        "READTHEDOCS": True,
        "github_user": "Gurobi",
        "github_repo": "gurobipy-pandas",
        "github_version": "main",
        "display_github": True,
        "conf_py_path": "/docs/source/",
    }

    # Set the canonical URL to always point to the stable version docs
    rtd_version = os.environ.get("READTHEDOCS_VERSION")
    rtd_url = os.environ.get("READTHEDOCS_CANONICAL_URL")
    html_baseurl = rtd_url.replace(rtd_version, "stable")


html_theme_options = {
    # Add Gurobi and Github icons to the footer
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://www.gurobi.com",
            "html": """
                <svg id="Layer_2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128.5 127.5"><defs><style>.cls-1{fill:#ed3424;}.cls-2{fill:#c61814;}.cls-3{fill:#22222c;}</style></defs><g id="Layer_2-2"><polygon class="cls-2" points="94.5 6.86 59.08 0 12.07 30.33 74.92 49.88 94.5 6.86"/><polygon class="cls-1" points="9.3 34.11 6.36 53.16 0 94.45 77.03 121.14 95.78 127.64 74.33 54.35 9.3 34.11"/><polygon class="cls-2" points="97.79 10.33 78.49 52.75 100.14 126.74 128.5 98.36 97.79 10.33"/></g></svg>
            """,
            "class": "",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/Gurobi/gurobipy-pandas",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}
