"""
========================================================================
GetGiveIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou
  Date: Mar 19, 2019
"""
import greenlet

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs

from .ifcs_utils import enrdy_to_str

#-------------------------------------------------------------------------
# GetIfcRTL
#-------------------------------------------------------------------------

class GetIfcRTL( Interface ):

  def construct( s, Type ):
    s.MsgType = Type

    s.msg = InPort ( Type )
    s.en  = OutPort( int if Type is int else Bits1 )
    s.rdy = InPort ( int if Type is int else Bits1 )

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# GiveIfcRTL
#-------------------------------------------------------------------------

class GiveIfcRTL( Interface ):

  def construct( s, Type ):
    s.MsgType = Type

    s.msg = OutPort( Type )
    s.en  = InPort ( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

class GetIfcFL( Interface ):

  def construct( s ):
    s.method = CallerPort()

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def line_trace( s ):
    return ''

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing SendCL (other) -> [ RecvCL -> GiveIfcFL ] -> GetIfcFL (s)
    # SendCL is a caller interface
    if isinstance( other, NonBlockingCallerIfc ):
      m = RecvCL2GiveFL()

      if hasattr( parent, "RecvCL2GiveFL_count" ):
        count = parent.RecvCL2GiveFL_count
        setattr( parent, "RecvCL2GiveFL_" + str( count ), m )
      else:
        parent.RecvCL2GiveFL_count = 0
        parent.RecvCL2GiveFL_0 = m

      connect_pairs(
        other,  m.recv,
        m.give, s
      )
      parent.RecvCL2GiveFL_count += 1
      return True

    return False

class GiveIfcFL( Interface ):

  def construct( s, method ):
    s.method = CalleePort( method=method )

  def line_trace( s ):
    return ''

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s.line_trace()

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2GiveFL( Component ):

  @blocking
  def give( s ):
    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)
    ret = s.entry
    s.entry = None
    return ret

  @non_blocking( lambda s : s.entry is None )
  def recv( s, msg ):
    s.entry = msg

  def construct( s ):

    # Interface

    s.give = GiveIfcFL( s.give )

    s.entry = None

    s.add_constraints( M( s.recv ) == M( s.give ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.give )
