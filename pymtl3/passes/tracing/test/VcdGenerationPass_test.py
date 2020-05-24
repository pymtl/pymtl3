#=========================================================================
# VcdGenerationPass_test.py
#=========================================================================
# Perform limited tests on the VCD generation pass. These tests are limited
# in the sense that they do not compare the entire output against some
# reference output, which is hard to obtain in the case of VCD generation.
# Our goal is to have some regression test cases that can hopefully inform
# us of any incompatible changes that lead to the failure of VCD generation
# during a major update of PyMTL.
#
# Author: Peitian Pan
# Date:   Nov 1, 2019

from pymtl3.datatypes import *
from pymtl3.dsl import *
from pymtl3.passes.PassGroups import DefaultPassGroup

from ..VcdGenerationPass import VcdGenerationPass


def run_test( dut, tv, tv_in, tv_out ):
  vcd_file_name = dut.__class__.__name__ + "_funky"
  dut.set_metadata( VcdGenerationPass.vcd_file_name, vcd_file_name )
  dut.apply( DefaultPassGroup() )
  for v in tv:
    tv_in( dut, v )
    dut.sim_tick()
    tv_out( dut, v )
  with open(vcd_file_name+".vcd") as fd:
    file_str = ''.join( fd.readlines() )
    all_signals = dut.get_input_value_ports() + \
                  dut.get_output_value_ports() + \
                  dut.get_wires()
    for signal in all_signals:
      assert signal._dsl.my_name in file_str

def test_vector_signals():
  class A( Component ):
    def construct( s ):
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.out = OutPort( Bits32 )

      @update
      def add_upblk():
        s.out @= s.in0 + s.in1
  def tv_in( m, tv ):
    m.in0 @= tv[0]
    m.in1 @= tv[1]
  def tv_out( m, tv ):
    assert m.out == tv[2]

  run_test( A(), [
    #     in0      in1      out
    [  b32(0), b32(-1), b32(-1), ],
    [  b32(1),  b32(1),  b32(2), ],
    [ b32(-1),  b32(0), b32(-1), ],
    [ b32(-1),  b32(0), b32(-1), ],
    [ b32(-1),  b32(0), b32(-1), ],
    [ b32(-1),  b32(0), b32(-1), ],
    [ b32(42), b32(42), b32(84), ],
  ], tv_in, tv_out )

def test_bitstruct_signals():
  bs = mk_bitstruct( "BitStructType", {
    'foo' : Bits1,
    'bar' : Bits32,
  } )

  class A2( Component ):
    def construct( s ):
      s.in0 = InPort( bs )
      s.in1 = InPort( Bits32 )
      s.out = OutPort( Bits32 )

      @update
      def add_upblk():
        s.out @= s.in0.bar + s.in1
  def tv_in( m, tv ):
    m.in0 @= tv[0]
    m.in1 @= tv[1]
  def tv_out( m, tv ):
    assert m.out == tv[2]

  run_test( A2(), [
    #     in0                 in1      out
    [  bs(0, 0),  b32(-1), b32(-1), ],
    [  bs(0, 1),  b32(1),  b32(2), ],
    [  bs(0, -1), b32(0), b32(-1), ],
    [  bs(0, 42), b32(42), b32(84), ],
  ], tv_in, tv_out )
