#=========================================================================
# YosysBehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.datatypes import Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL4_test import (
    test_interface,
    test_interface_index,
)

from ..YosysBehavioralTranslatorL4 import YosysBehavioralRTLIRToSVVisitorL4


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = YosysBehavioralRTLIRToSVVisitorL4(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs_yosys[blk.__name__]

def test_interface_array_non_static_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[s.in_[0].foo].foo
  a = A()
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in___foo[in___foo[0]];
end\
""" }
  do_test( a )
