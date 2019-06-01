#=======================================================================
# simple_reg_test.py
#=======================================================================

from pymtl3 import *

from pymtl3.passes.sverilog.import_.ImportPass import ImportPass
from pymtl3.passes.PassGroups import *
import os
import random
import pytest

def test_VReg( dump_vcd ):

  class VReg( Component ):
    sourcefile = "VReg.sv"

    def construct( s ):
      s.in_ = InPort ( Bits32 )
      s.out = OutPort( Bits32 )

      s.sv_port_mapping = {
        'clk' : s.clk,
        'd'   : s.in_,
        'q'   : s.out,
      }

  class Wrapper( Component ):
    def construct( s ):
      s.in_ = InPort ( Bits32 )
      s.out = OutPort( Bits32 )

      s.inner = VReg()( in_ = s.in_, out = s.out )

    def line_trace( s ):
      return "{} > {}".format( s.in_, s.out )

  #---------------------------------------------------------------------
  # test
  #---------------------------------------------------------------------

  m = Wrapper()
  dtype = Bits32

  m.elaborate()

  m.apply( ImportPass() ),

  m.apply( GenDAGPass() ),
  m.apply( WrapGreenletPass() ),
  m.apply( DynamicSchedulePass() ),
  m.apply( SimpleTickPass() ),
  m.lock_in_simulation()

  m.sim_reset()

  for i in range( 10 ):
    m.in_ = dtype( i )
    m.tick()
    print m.line_trace()
    assert m.out == i
