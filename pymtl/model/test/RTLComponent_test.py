#=========================================================================
# RTLComponent_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Dec 25, 2017

from pymtl import *
from pymtl.model.errors import MultiWriterError, InvalidConnectionError
from pclib.rtl import TestBasicSource as TestSource, TestBasicSink as TestSink
from pclib.rtl import Mux
from sim_utils import simple_sim_pass

MUX_SEL_0 = 0
MUX_SEL_1 = 1

def test_reset():

  class B(RTLComponent):
    def construct( s ):
      s.out = OutVPort( Bits32 )
      @s.update_on_edge
      def up_out():
        if s.reset:
          s.out = Bits32( 0x12345678 )
        else:
          s.out = Bits32( 0 )

  class Top(RTLComponent):
    def construct( s ):
      s.b = B()

      @s.update
      def up_tmp():
        print s.b.out

  top = Top()
  top.elaborate()
  simple_sim_pass( top, 0x123 )
  top.sim_reset()
