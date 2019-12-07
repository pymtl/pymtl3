#=========================================================================
# TranslationImport_dynlib_close_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Dec 6, 2019
"""Test if the shared library was closed at the end of simulation."""

from pymtl3 import *
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test import TestVectorSimulator

from .. import TranslationImportPass
from ..import_.ImportConfigs import ImportConfigs
from ..util.utility import get_file_hash


def run_test( _m ):
  try:
    _m.elaborate()
    _m.sverilog_translate_import = True
    _m.config_sverilog_import = \
        ImportConfigs(vl_Wno_list=['UNOPTFLAT', 'UNSIGNED'], vl_trace=True)
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
    sim.run_test()
  finally:
    try:
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass

def test_dynlib_close():
  class Comb:
    class A( Component ):
      def construct( s ):
        s.in_ = InPort( Bits32 )
        s.out = OutPort( Bits32 )
        @s.update
        def upblk():
          s.out = s.in_
  class Seq:
    class A( Component ):
      def construct( s ):
        s.in_ = InPort( Bits32 )
        s.out = OutPort( Bits32 )
        @s.update_ff
        def upblk():
          s.out <<= s.in_

  comb_a = Comb.A()
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  comb_a._test_vectors = [
    [    0,   0  ],
    [   42,   42 ],
    [   24,   24 ],
    [   -2,   -2 ],
    [   -1,   -1 ],
  ]
  comb_a._tv_in, comb_a._tv_out = tv_in, tv_out
  run_test( comb_a )
  comb_hash = get_file_hash('A.verilator1.vcd')

  seq_a = Seq.A()
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    if tv[1] != '*':
      assert m.out == Bits32(tv[1])
  seq_a._test_vectors = [
    [    0,   '*' ],
    [   42,    0  ],
    [   24,    42 ],
    [   -2,    24 ],
    [   -1,    -2 ],
  ]
  seq_a._tv_in, seq_a._tv_out = tv_in, tv_out
  run_test( seq_a )
  seq_hash = get_file_hash('A.verilator1.vcd')

  assert comb_hash != seq_hash
