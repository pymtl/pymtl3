#=========================================================================
# SVBehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from __future__ import absolute_import, division, print_function

from pymtl import Bits1, Bits32, Component, InPort, Interface, OutPort, concat
from pymtl.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL4 import (
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
  do_test( a )

def test_interface_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in xrange(2) ]
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
  do_test( a )
