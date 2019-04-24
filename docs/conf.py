# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import sys
import os
import shlex
import subprocess
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))
import sphinx_rtd_theme
import re
import numpy as np
import starry


def sort_props(doc):
    """Sort the attributes and methods in a docstring."""
    attributes = re.findall('(.. autoattribute:: .*?)\n', doc)
    methods = re.findall('(.. automethod:: .*?)\n', doc)
    props = attributes + methods
    props.sort(key=lambda x: x[x.index(':'):].lower())
    props = "\n".join(props)
    return props


# Hack: instantiate some Maps to fudge their docstrings
map = starry.Map(ydeg=1, udeg=1, fdeg=1)
starry.Map = type('Map', map.__class__.__bases__, dict(map.__class__.__dict__))
starry.Map.__doc__ = starry.Map.__descr__() + sort_props(starry.Map.__doc__)

map = starry.DopplerMap(ydeg=1, udeg=1)
starry.DopplerMap = type('DopplerMap', map.__class__.__bases__, dict(map.__class__.__dict__))
starry.DopplerMap.__doc__ = starry.DopplerMap.__descr__() + sort_props(starry.DopplerMap.__doc__)


# -- Project information -----------------------------------------------------

project = 'starry'
copyright = '2019, Rodrigo Luger'
author = 'Rodrigo Luger'

# The short X.Y version
version = starry.__version__
# The full version, including alpha/beta/rc tags
release = starry.__version__


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'matplotlib.sphinxext.plot_directive',
    'nbsphinx'
]

# Build Doxygen docs
subprocess.call(['doxygen', 'Doxyfile'])
html_extra_path = ['.doxyxml/']

# NBSphinx
nbsphinx_prolog = """
{% set docname = env.doc2path(env.docname, base=None) %}

.. note:: This tutorial was generated from an Jupyter notebook that can be
          downloaded `here <https://github.com/rodluger/starry/blob/master/docs/{{ docname }}>`_.
"""

# Autosummary
autosummary_generate = True

# Autodoc
autodoc_docstring_signature = True

# Remove jupyter notebook prompt numbers
nbsphinx_prompt_width = 0
napoleon_use_ivar = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['.templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ['.build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
if not on_rtd:  # only import and set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = ['.themes',]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['.static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'starrydoc'

# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True