"""
========================================================================
SendRecvIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou, Shunning Jiang
  Date: May 5, 2019
"""
from copy import deepcopy

import greenlet

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs

from .ifcs_utils import enrdy_to_str

#-------------------------------------------------------------------------
# RecvIfcRTL
#-------------------------------------------------------------------------

class RecvIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg =  InPort( Type )
    s.en  =  InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

    s.MsgType = Type

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing SendCL (other) -> [ RecvCL -> SendRTL ] -> RecvRTL (s)
    # SendCL is a caller interface
    if isinstance( other, NonBlockingCallerIfc ):
      m = RecvCL2SendRTL( s.MsgType )

      if hasattr( parent, "RecvCL2SendRTL_count" ):
        count = parent.RecvCL2SendRTL_count
        setattr( parent, "RecvCL2SendRTL_" + str( count ), m )
      else:
        parent.RecvCL2SendRTL_count = 0
        parent.RecvCL2SendRTL_0 = m

      connect_pairs(
        other,  m.recv,
        m.send.msg, s.msg,
        m.send.en,  s.en,
        m.send.rdy, s.rdy
      )
      parent.RecvCL2SendRTL_count += 1
      return True

    return False

#-------------------------------------------------------------------------
# SendIfcRTL
#-------------------------------------------------------------------------

class SendIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.en  = OutPort( int if Type is int else Bits1 )
    s.rdy =  InPort( int if Type is int else Bits1 )

    s.MsgType = Type

  def line_trace( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( "{}".format( s.MsgType() ) )
      trace_len = s.trace_len

    return enrdy_to_str( s.msg, s.en, s.rdy, trace_len )

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing SendRTL (s) -> [ RecvRTL -> SendCL ] -> RecvCL (other)
    # RecvCL is a callee interface
    if isinstance( other, NonBlockingCalleeIfc ):
      m = RecvRTL2SendCL( s.MsgType )

      if hasattr( parent, "RecvRTL2SendCL_count" ):
        count = parent.RecvRTL2SendCL_count
        setattr( parent, "RecvRTL2SendCL_" + str( count ), m )
      else:
        parent.RecvRTL2SendCL_count = 0
        parent.RecvRTL2SendCL_0 = m

      connect_pairs(
        m.send, other,
        s.msg, m.recv.msg,
        s.en,  m.recv.en,
        s.rdy, m.recv.rdy,
      )
      parent.RecvRTL2SendCL_count += 1
      return True

    return False


class SendIfcFL( Interface ):

  def construct( s ):
    s.method = CallerPort()

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def line_trace( s ):
    return ''

  def __str__( s ):
    return s.line_trace()

  def connect( s, other, parent ):

    # We are doing SendFL (s) -> [ RecvFL -> SendCL ] -> RecvCL (s)
    # SendCL is a caller interface
    # FIXME direction
    if isinstance( other, NonBlockingCallerIfc ) or \
       isinstance( other, NonBlockingCalleeIfc ):
      m = RecvFL2SendCL()

      if hasattr( parent, "RecvFL2SendCL_count" ):
        count = parent.RecvFL2SendCL_count
        setattr( parent, "RecvFL2SendCL_" + str( count ), m )
      else:
        parent.RecvFL2SendCL_count = 0
        parent.RecvFL2SendCL_0 = m

      connect_pairs(
        s,      m.recv,
        m.send, other,
      )
      parent.RecvFL2SendCL_count += 1
      return True

    return False

class RecvIfcFL( Interface ):

  def construct( s, method ):
    s.method = CalleePort( method=method )

  def line_trace( s ):
    return ''

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s.line_trace()


"""
========================================================================
Send/RecvIfc adapters
========================================================================
CL/RTL adapters for send/recv interface.

Author : Yanghui Ou
  Date : Mar 07, 2019
"""

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2SendRTL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.send = SendIfcRTL( MsgType )

    s.entry = None

    @s.update
    def up_clear():
      if s.send.en: # constraints reverse this
        s.entry = None

    @s.update
    def up_send_rtl():
      if s.entry is None:
        s.send.en  = Bits1( 0 )
        s.send.msg = MsgType()
      else:
        s.send.en  = s.send.rdy
        s.send.msg = s.entry

    s.add_constraints(
      U( up_clear )   < WR( s.send.en ),
      U( up_clear )   < M( s.recv ),
      U( up_clear )   < M( s.recv.rdy ),
      M( s.recv )     < U( up_send_rtl ),
      M( s.recv.rdy ) < U( up_send_rtl )
    )

  @non_blocking( lambda s : s.entry is None )
  def recv( s, msg ):
    s.entry = deepcopy(msg)

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )
    s.send = NonBlockingCallerIfc()

    s.sent_msg = None
    s.send_rdy = False

    @s.update
    def up_recv_rtl_rdy():
      s.send_rdy = s.send.rdy() and not s.reset
      s.recv.rdy = Bits1( 1 ) if s.send.rdy() and not s.reset else Bits1( 0 )

    @s.update
    def up_send_cl():
      s.sent_msg = None
      if s.recv.en:
        s.send( s.recv.msg )
        s.sent_msg = s.recv.msg

    s.add_constraints( U( up_recv_rtl_rdy ) < U( up_send_cl ) )

  def line_trace( s ):
    return "{}(){}".format(
      s.recv.line_trace(),
      enrdy_to_str( s.sent_msg, s.sent_msg is not None, s.send_rdy )
    )

#-------------------------------------------------------------------------
# RecvFL2SendCL
#-------------------------------------------------------------------------

class RecvFL2SendCL( Component ):

  @blocking
  def recv( s, msg ):
    while not s.send.rdy():
      greenlet.getcurrent().parent.switch(0)
    assert s.send.rdy()
    s.send( msg )

  def construct( s ):

    # Interface

    s.recv = RecvIfcFL( s.recv )
    s.send = NonBlockingCallerIfc()

    s.add_constraints( M( s.recv ) == M( s.send ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )
