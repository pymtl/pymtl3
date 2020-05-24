"""
========================================================================
ValRdyIfc
========================================================================
RTL val/rdy interface.

Author : Shunning Jiang
  Date : Apr 5, 2019
"""
from typing import Generic, TypeVar

from pymtl3 import *


def valrdy_to_str( msg, val, rdy, trace_len=15 ):
  if     val and not rdy: return "#".ljust( trace_len )
  if not val and     rdy: return " ".ljust( trace_len )
  if not val and not rdy: return ".".ljust( trace_len )
  return f"{msg}".ljust( trace_len ) # val and rdy

T_InValRdyIfc = TypeVar("T_InValRdyIfc")

class InValRdyIfc( Interface, Generic[T_InValRdyIfc] ):

  def construct( s ):

    s.msg = InPort[T_InValRdyIfc]()
    s.val = InPort[Bits1]()
    s.rdy = OutPort[Bits1]()

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

T_OutValRdyIfc = TypeVar("T_OutValRdyIfc")

class OutValRdyIfc( Interface, Generic[T_OutValRdyIfc] ):

  def construct( s ):

    s.msg = OutPort[T_OutValRdyIfc]()
    s.val = OutPort[Bits1]()
    s.rdy = InPort[Bits1]()

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )
