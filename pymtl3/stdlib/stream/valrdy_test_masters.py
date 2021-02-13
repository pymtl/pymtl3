"""
==========================================================================
 test_masters.py
==========================================================================

 Author: Shunning Jiang
   Date: May 27, 2020
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs.valrdy_master_minion_ifcs import MasterIfcRTL

from .valrdy_test_sinks import TestSinkRTL
from .valrdy_test_srcs import TestSrcRTL


class TestMasterRTL( Component ):

  def construct( s, ReqType, RespType, MasterIfc=MasterIfcRTL ):
    s.master = MasterIfc( ReqType, RespType )
    s.src  = TestSrcRTL( ReqType )
    s.sink = TestSinkRTL( RespType )

    s.src.out  //= s.master.req
    s.sink.in_ //= s.master.resp

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return str(s.master)
