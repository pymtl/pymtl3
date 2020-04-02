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

def pytest_addoption(parser):
  group = parser.getgroup("pytest-pymtl3")
  group.addoption( "--test-verilog", dest="test_verilog", action="store",
                    default='', nargs='?', const='zeros',
                    help="run verilog translation" )
  group.addoption( "--dump-vcd", dest="dump_vcd", action="store_true",
                    default=False, help="dump vcd for each test" )

def _any_option_present( config ):
  option_default_pair = [
      ( 'dump_vcd',     False ),
      ( 'test_verilog', ''    ),
  ]
  return any(config.getoption(opt) != val for opt, val in option_default_pair)

def _parse_config_from_request( request ):
  cfg = {}

  # test_verilog
  test_verilog = request.config.getoption("test_verilog")
  try:
    test_verilog = int(test_verilog)
  except ValueError:
    assert test_verilog in ['', 'zeros', 'ones', 'rand'], \
        f"--test-verilog should be an int or one of '', 'zeros', 'ones', 'rand'!"
  cfg['test_verilog'] = test_verilog

  # dump_vcd
  dump_vcd = request.config.getoption("dump_vcd")
  if dump_vcd:
    test_module = request.module.__name__
    test_name   = request.node.name
    dump_vcd    = f"{test_module}.{test_name}.vcd"
  cfg['dump_vcd'] = dump_vcd

  return cfg

@pytest.fixture
def pymtl_config( request ):
  """PyMTL configuration parsed from pytest commandline options."""
  return _parse_config_from_request( request )

@pytest.fixture
def pymtl_no_translation( request ):
  cfg = _parse_config_from_request( request )
  if cfg['test_verilog']:
    pytest.skip("non-translatable test skipped when --test-verilog is enabled")

# def pytest_configure(config):
#   from pymtl3.extra import pytest as pytest_options
#   pytest_options.called_from_pytest = True
#   if config.getoption('test_verilog'):
#     pytest_options.test_verilog = config.getoption('test_verilog')
#   if config.getoption('dump_vcd'):
#     pytest_options.test_verilog = config.getoption('dump_vcd')

# def pytest_unconfigure(config):
#   from pymtl3.extra import pytest as pytest_options
#   pytest_options.called_from_pytest = None
#   pytest_options.dump_vcd           = None
#   pytest_options.test_verilog       = None

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  if _any_option_present( item.config ) and 'pymtl_config' not in item.funcargnames:
    pytest.skip("'pymtl_config' is required by pytest command but not used by test")
