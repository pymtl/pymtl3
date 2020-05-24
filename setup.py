"""
========================================================================
setup.py
========================================================================
setup.py inspired by the PyPA sample project:
https://github.com/pypa/sampleproject/blob/master/setup.py
"""


from os import path

from setuptools import find_packages, setup

#-------------------------------------------------------------------------
# get_version
#-------------------------------------------------------------------------

def get_version():
  # Check Python version compatibility
  import sys
  assert sys.version_info[0] > 2, "Python 2 is no longer supported!"

  _d = {}
  with open(path.join(path.dirname(__file__), "pymtl3/version.py")) as f:
    exec(f.read(), _d)
  return _d['__version__']

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

  name                          = 'pymtl3',
  version                       = get_version(),
  description                   = \
      'PyMTL 3 (Mamba): A Python-based hardware generation, simulation, and verification framework',
  long_description              = get_long_description(),
  long_description_content_type = "text/markdown",
  url                           = 'https://github.com/pymtl/pymtl3',
  author                        = 'Batten Research Group',
  author_email                  = 'brg-pymtl@csl.cornell.edu',

  # BSD 3-Clause License:
  # - http://choosealicense.com/licenses/bsd-3-clause
  # - http://opensource.org/licenses/BSD-3-Clause

  license='BSD',

  # Pip will block installation on unsupported versions of Python
  python_requires=">=3.6",

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
  classifiers=[
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3 :: Only',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
    'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
  ],

  packages = find_packages(
    exclude=['scripts', 'examples', 'examples.*', 'examples.*.*']
  ),

  package_data={
    'pymtl3': [
      # 'passes/backends/verilog/import_/verilator_wrapper.c.template',
      # 'passes/backends/verilog/import_/verilator_wrapper.py.template',
      # 'passes/backends/verilog/tbgen/verilog_tbgen.v.template',
    ],
  },

  install_requires = [
    'pytest',
    'hypothesis >= 4.18.1',
    'cffi',
    'greenlet',
  ],

  entry_points = {
    'pytest11' : [
      'pytest-pymtl3 = pytest_plugin.pytest_pymtl3',
    ]
  }

)
