"""
========================================================================
setup.py
========================================================================
setup.py inspired by the PyPA sample project:
https://github.com/pypa/sampleproject/blob/master/setup.py
"""

from __future__ import absolute_import, division, print_function

from codecs import open  # To use a consistent encoding
from os import path
from subprocess import check_output

from setuptools import find_packages, setup

#-------------------------------------------------------------------------
# get_version
#-------------------------------------------------------------------------

def get_version():
  result = "?"
  with open("pymtl3/__init__.py") as f:
    for line in f:
      if line.startswith("__version__"):
        _, result, _ = line.split('"')
  return result

#-------------------------------------------------------------------------
# get_long_descrption
#-------------------------------------------------------------------------

def get_long_description():
  here = path.abspath(path.dirname(__file__))
  with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    return f.read()

#-------------------------------------------------------------------------
# setup
#-------------------------------------------------------------------------

setup(

  name             = 'pymtl3',
  version          = get_version(),
  description      = 'PyMTL 3 (Mamba): Python-based hardware generation, simulation, and verification framework',
  long_description = get_long_description(),
  long_description_content_type="text/markdown",
  url              = 'https://github.com/cornell-brg/pymtl3',
  author           = 'Batten Research Group',
  author_email     = 'brg-pymtl@csl.cornell.edu',

  # BSD 3-Clause License:
  # - http://choosealicense.com/licenses/bsd-3-clause
  # - http://opensource.org/licenses/BSD-3-Clause

  license='BSD',

  # Pip will block installation on unsupported versions of Python
  python_requires=">=2.7",

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
  classifiers=[
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 2.7',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
  ],

  packages = find_packages(
    exclude=['scripts', 'examples', 'examples.*', 'examples.*.*']
  ),

  package_data={
    'pymtl3': [
      'passes/sverilog/import_/verilator_wrapper.c.template',
      'passes/sverilog/import_/verilator_wrapper.py.template',
    ],
  },

  install_requires = [
    'pytest',
    'hypothesis >= 4.18.1',
    'pytest-xdist',
    'cffi',
    'greenlet',
    'pyparsing',
    'graphviz'
  ],

)
