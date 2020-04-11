#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Test ad-hoc components with SystemVerilog translation and import."""

import gc
import resource

import pytest

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogPlaceholderPass
from pymtl3.passes.rtlir.util.test_utility import get_parameter
from pymtl3.stdlib.test import TestVectorSimulator

from .. import TranslationImportPass


# args: [attr, Bits, idx]
def _set( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_in_str = 'def tv_in( m, tv ):  \n'
  if len(args) == 0:
    _tv_in_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    if isinstance(Bits, str):
      _tv_in_str += f'  m.{attr} = {Bits}( tv[{idx}] )\n'
    else:
      _tv_in_str += f'  m.{attr} = {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_in_str, globals(), local_dict )
  return local_dict['tv_in']

# args: [attr, Bits, idx]
def _check( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_out_str = 'def tv_out( m, tv ):  \n'
  if len(args) == 0:
    _tv_out_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    if isinstance(Bits, str):
      _tv_out_str += f'  assert m.{attr} == {Bits}( tv[{idx}] )\n'
    else:
      _tv_out_str += f'  assert m.{attr} == {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_out_str, globals(), local_dict )
  return local_dict['tv_out']

class CasePlusOneComp:
  class DUT( Component ):
    def construct( s ):
      s.mem = bytearray(1<<26)
      s.mem[-1]=1
      s.mem[-2]=123
      s.mem[1] =12
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_ + 1
    def line_trace( s ):
      return f"{s.in_} > {s.out}"
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TEST_VECTOR = \
  [
      [    0,    1 ],
      [   42,   43 ],
      [   24,   25 ],
      [   -2,   -1 ],
      [   -1,    0 ],
  ]

def run_test( case ):
  gc.collect()
  m = case.DUT()
  m.elaborate()
  m.verilog_translate_import = True
  m.apply( VerilogPlaceholderPass() )
  m = TranslationImportPass()( m )

  sim = TestVectorSimulator( m, case.TEST_VECTOR, case.TV_IN, case.TV_OUT )
  sim.run_test()

  m.finalize()
  gc.collect()
  print("python process memory usage:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024," MB")

@pytest.mark.parametrize(
  'case', [ CasePlusOneComp ] * 3,
)
def test_verilog_translation_import_adhoc( case ):
  run_test( case )
