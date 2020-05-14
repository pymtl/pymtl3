# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import os
import sphinx_rtd_theme

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# -- Project information -----------------------------------------------------

project   = 'PyMTL3'
copyright = f'2017-{datetime.datetime.utcnow().year}, Batten Research Group'
author    = 'Batten Research Group'

_d = {}
with open(
    os.path.join(os.path.dirname(__file__), '..', 'pymtl3', 'version.py')
) as fd:
  exec(fd.read(), _d)
  version = _d['__version__']
  release = _d['__version__']

# extlinks provide convenient aliases for long URLs
# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
_repo    = 'https://github.com/cornell-brg/pymtl3'
extlinks = {
    'commit'  : (_repo + 'commit/%s', 'commit '),
    'gh-file' : (_repo + 'blob/master/%s', ''),
    'gh-link' : (_repo + '%s', ''),
    'issue'   : (_repo + 'issues/%s', 'issue #'),
    'pull'    : (_repo + 'pull/%s', 'pull request #'),
    'pypi'    : ('https://pypi.org/project/%s', ''),
}


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'recommonmark',
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.extlinks',
    'sphinx.ext.napoleon',
    'sphinx-prompt',
]

# Use `index.rst` as the top level documentation.
master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# HTML options
html_theme_options = {
    'navigation_depth' : 2,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ['_static']
