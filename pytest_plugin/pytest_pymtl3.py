#=========================================================================
# pytest_pymtl3.py
#=========================================================================
# PyMTL3 pytest plugin. Reused the conftest.py file from pymtl3 repo.
# With the current setup, you can add `pytest_plugins = "pytest_pymtl3"`
# to obtain access to the pytest fixtures defined below.
#
# Author : Peitian Pan
# Date   : March 30, 2020

import os

import pytest

if 'CI' in os.environ:
  # Set up the CI hypothesis profile which limits the max number of tries
  # The 'CI' profile will be specified through the testing command of the
  # CI script.
  from hypothesis import settings
  settings.register_profile("CI", max_examples=10)

#-------------------------------------------------------------------------
# pytest hooks and fixtures
#-------------------------------------------------------------------------

def pytest_addoption(parser):
  group = parser.getgroup("pytest-pymtl3")
  group.addoption( "--test-verilog", dest="test_verilog", action="store",
                    default='', nargs='?', const='zeros',
                    help="run verilog translation" )
  group.addoption( "--dump-vcd", dest="dump_vcd", action="store_true",
                    default=None, help="dump vcd for each test" )
  group.addoption( "--dump-vtb", dest="dump_vtb", action="store_true",
                    default=None, help="dump verilog test bench for each test" )
  group.addoption( "--max-cycles", dest="max_cycles", action="store",
                    default=None, help="max cycles of simulation" )

@pytest.fixture
def cmdline_opts( request ):
  """PyMTL options parsed from pytest commandline options."""
  opts = _parse_opts_from_request( request )

  # If a fixture is used by a test class, this seems to be the only
  # way to retrieve the fixture value.
  # https://stackoverflow.com/a/37761165/13190001
  if request.cls is not None:
    request.cls.cmdline_opts = opts

  return opts

@pytest.fixture
def no_translation( request ):
  """Mark a test case as not to be translated."""
  opts = _parse_opts_from_request( request )
  if opts['test_verilog'] != '':
    pytest.skip("skipping untranslatable test cases with --test-verilog")

def pytest_configure(config):
  pass

def pytest_unconfigure(config):
  pass

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  if _any_opts_present(item.config) and 'cmdline_opts' not in item.fixturenames:
    pytest.skip("'cmdline_opts' is required by pytest commandline but not used")

#-------------------------------------------------------------------------
# helper functions
#-------------------------------------------------------------------------

def _any_opts_present( config ):
  opt_default_pairs = [
      ( 'test_verilog', ''    ),
      ( 'dump_vcd',     None ),
      ( 'dump_vtb',     None ),
      ( 'max_cycles',   None ),
  ]
  return any([config.getoption(opt) != val for opt, val in opt_default_pairs])

def _parse_opts_from_request( request ):
  opts = {}

  # test_verilog
  test_verilog = request.config.getoption("test_verilog")
  try:
    test_verilog = int(test_verilog)
  except ValueError:
    assert test_verilog in ['', 'zeros', 'ones', 'rand'], \
        "--test-verilog should be an int or one of '', 'zeros', 'ones', 'rand'!"
  opts['test_verilog'] = test_verilog

  # dump_vcd
  dump_vcd = request.config.getoption("dump_vcd")
  if dump_vcd:
    test_module = request.module.__name__
    test_name   = request.node.name.replace('-', '_').replace( '[', '_' ).replace( ']', '' )
    dump_vcd = f'{test_module}__{test_name}'
  else:
    dump_vcd = ''
  opts['dump_vcd'] = dump_vcd

  # dump_vtb
  dump_vtb = request.config.getoption("dump_vtb")
  if dump_vtb:
    assert request.config.getoption("test_verilog"), "--dump-vtb requires --test-verilog"
    test_module = request.module.__name__
    test_name   = request.node.name
    dump_vtb    = test_name.replace('-', '_').replace( '[', '_' ).replace( ']', '' )
  else:
    dump_vtb = ''
  opts['dump_vtb'] = dump_vtb

  # max_cycles
  max_cycles = request.config.getoption("max_cycles")
  if max_cycles is not None:
    try:
      max_cycles = int(max_cycles)
    except ValueError:
      raise Exception("command line option `--max-cycles` should have integer value!")
  opts['max_cycles'] = max_cycles

  return opts
