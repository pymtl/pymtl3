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

def pytest_addoption(parser):
  group = parser.getgroup("pytest_pymtl3")
  group.addoption( "--test-verilog", dest="test_verilog", action="store",
                    default='', nargs='?', const='zeros',
                    choices=[ '', 'zeros', 'ones', 'rand' ],
                    help="run verilog translation, " )
  group.addoption( "--dump-vcd", dest="dump_vcd", action="store_true",
                    default=False,
                    help="dump vcd for each test" )

@pytest.fixture
def test_verilog(request):
  """Test Verilog translation rather than python."""
  return request.config.getoption("test_verilog")

@pytest.fixture
def dump_vcd(request):
  """Dump VCD for each test."""
  if request.config.getoption("dump_vcd"):
    test_module = request.module.__name__
    test_name   = request.node.name
    return '{}.{}.vcd'.format( test_module, test_name )
  else:
    return ''

def pytest_configure(config):
  import sys
  sys._called_from_test = True
  if config.getoption('dump_vcd'):
    sys._pymtl_dump_vcd = True
  else:
    sys._pymtl_dump_vcd = False

def pytest_unconfigure(config):
  import sys
  del sys._called_from_test
  del sys._pymtl_dump_vcd

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  test_verilog = item.config.getoption("test_verilog")
  if test_verilog and 'test_verilog' not in item.funcargnames:
    pytest.skip("ignoring non-Verilog tests")
