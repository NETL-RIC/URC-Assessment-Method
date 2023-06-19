# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

from urclib import __version__ as urc_version
# -- Project information -----------------------------------------------------

project = 'URC Resource Assessment Method Tool Documentation'
copyright = '2023, NETL-RIC'
author = 'NETL-RIC'
version = f'Version: {urc_version}'

import sphinx_rtd_theme
import os
import sys

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [ 
'sphinx.ext.napoleon',       # For google-code and numpy style docstrings
'sphinx.ext.autodoc',
'sphinx.ext.mathjax',        # For embedding math equations in output html
'sphinx.ext.todo',           # Enables TO-DO lists
'sphinx_rtd_theme',          # HTML theme from read-the-docs
'myst_parser',               # Adds support for markdown (.md) files (need to install myst-parser)
'sphinxcontrib.bibtex',       # Allows usable of the bibtex extension for sphinx
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# bibtex configuration
bibtex_bibfiles = ['lit_references.bib']
bibtex_default_style = 'alpha'
bibtex_reference_style = 'author_year'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Suffix control for parsers
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
}


# MyST markdown extras
myst_enable_extensions = [
    "amsmath", # for LateX equations.
    "deflist", # For definition list syntax
]

# for enableing auto-generated header anchors
myst_heading_anchors = 3


# -- Options for autodoc output ----------------------------------------------

sys.path.insert(0,os.path.abspath('../..'))

autodoc_mock_imports=['osgeo','osgeo.gdal','osgeo.ogr','osgeo.osr','glm','PyOpenGL.GL','numpy','pandas','pyside6']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# formatting details for html theme
html_logo = '_static/urc_logo.png'
html_favicon='_static/urc_favicon.ico'
html_short_title='URCMethod'
html_show_sourcelink = False

