#=========================================================================
# SVBehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, concat
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL4 import (
    BehavioralRTLIRToSVVisitorL4,
)


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL4()
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

def test_interface( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.val = InPort( Bits1 )
      s.msg = InPort( Bits32 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.val = OutPort( Bits1 )
      s.msg = OutPort( Bits32 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      @s.update
      def upblk():
        s.out.val = s.in_.val
        s.out.msg = s.in_.msg
        s.in_.rdy = s.out.rdy
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out_$val = in__$val;
  out_$msg = in__$msg;
  in__$rdy = out_$rdy;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_.val = Bits1(tv[0])
    m.in_.msg = Bits32(tv[1])
    m.out.rdy = Bits1(1)
  def tv_out( m, tv ):
    assert m.in_.rdy == Bits1(1)
    assert m.out.val == Bits1(tv[2])
    assert m.out.msg == Bits32(tv[3])
  a._test_vectors = [
    [   1,      0,   1,      0 ],
    [   0,     42,   0,     42 ],
    [   1,     42,   1,     42 ],
    [   1,     -1,   1,     -1 ],
    [   1,     -2,   1,     -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_interface_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[1].foo
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in__$1_$foo;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0].foo = Bits32(tv[0])
    m.in_[1].foo = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[2])
  a._test_vectors = [
    [    0,    0,      0 ],
    [    0,   42,     42 ],
    [   24,   42,     42 ],
    [   -2,   -1,     -1 ],
    [   -1,   -2,     -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
