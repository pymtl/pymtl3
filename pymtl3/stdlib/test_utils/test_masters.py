"""
==========================================================================
 test_masters.py
==========================================================================

 Author: Shunning Jiang
   Date: May 27, 2020
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import MasterIfcCL

from .test_sinks import TestSinkCL
from .test_srcs import TestSrcCL


class TestMasterCL( Component ):

  def construct( s, ReqType, RespType, MasterIfc=MasterIfcCL ):
    s.master = MasterIfc( ReqType, RespType )
    s.src  = TestSrcCL( ReqType )
    s.sink = TestSinkCL( RespType )

    s.src.send  //= s.master.req
    s.sink.recv //= s.master.resp

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return str(s.master)
