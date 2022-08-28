"""
========================================================================
IStream and OStream interfaces
========================================================================
RTL IStream and OStream interface with val/rdy.

Author : Shunning Jiang, Peitian Pan
  Date : Aug 26, 2022
"""
from pymtl3 import *


def valrdy_to_str( msg, val, rdy, trace_len=15 ):
  if     val and not rdy: return "#".ljust( trace_len )
  if not val and     rdy: return " ".ljust( trace_len )
  if not val and not rdy: return ".".ljust( trace_len )
  return f"{msg}".ljust( trace_len ) # val and rdy

class IStreamIfc( Interface ):

  def construct( s, Type ):

    s.msg = InPort( Type )
    s.val = InPort()
    s.rdy = OutPort()

    s.trace_len = len(str(Type()))

  def __str__( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy, s.trace_len )

class OStreamIfc( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.val = OutPort()
    s.rdy = InPort()

    s.trace_len = len(str(Type()))

  def __str__( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy, s.trace_len )
