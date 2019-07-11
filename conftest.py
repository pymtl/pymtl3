from __future__ import absolute_import, division, print_function

import pytest


def pytest_addoption(parser):
  parser.addoption( "--test-verilog", action="store", default='', nargs='?', const='zeros', choices=[ '', 'zeros', 'ones', 'rand' ],
                    help="run verilog translation, " )
  parser.addoption( "--dump-vcd", action="store_true",
                    help="dump vcd for each test" )

@pytest.fixture
def test_verilog(request):
  """Test Verilog translation rather than python."""
  return request.config.option.test_verilog

@pytest.fixture
def dump_vcd(request):
  """Dump VCD for each test."""
  if request.config.option.dump_vcd:
    test_module = request.module.__name__
    test_name   = request.node.name
    return '{}.{}.vcd'.format( test_module, test_name )
  else:
    return ''

def pytest_configure(config):
  import sys
  sys._called_from_test = True
  if config.option.dump_vcd:
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
  test_verilog = item.config.option.test_verilog
  if test_verilog and 'test_verilog' not in item.funcargnames:
    pytest.skip("ignoring non-Verilog tests")
