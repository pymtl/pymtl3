"""
==========================================================================
 master_minion_ifc.py
==========================================================================
Master/minion send/recv interface implementations at CL and RTL.

 Author: Shunning Jiang
   Date: Jan 28, 2020
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import MasterIfcCL
from .test_srcs import TestSrcCL
from .test_sinks import TestSinkCL

class TestMasterCL( Component ):

  def construct( s, Types ):
    s.master = MasterIfcCL( Types )
    s.src  = TestSrcCL( Types.req )( send=s.master.req )
    s.sink = TestSinkCL( Types.resp )( recv=s.master.resp )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return str(s.master)
