"""
========================================================================
SendRecvIfc.py
========================================================================
RTL implementation of en/rdy micro-protocol.

Author: Yanghui Ou, Shunning Jiang
  Date: May 5, 2019
"""
import greenlet

from pymtl3 import *
from pymtl3.dsl.errors import InvalidConnectionError
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.connects import connect_pairs

#-------------------------------------------------------------------------
# RecvIfcRTL
#-------------------------------------------------------------------------

class RecvIfcRTL( CalleeIfcRTL ):

  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=Type, RetType=None )

  def connect( s, other, parent ):

    # We are doing SendCL (other) -> [ RecvCL -> SendRTL ] -> RecvRTL (s)
    # SendCL is a caller interface
    if isinstance( other, CallerIfcCL ):
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

    elif isinstance( other, CalleeIfcCL ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between RecvIfcRTL"
            " and CalleeIfcCL.\n"
            "          - level {}: {} (class {})\n"
            "          - level {}: {} (class {})".format(
                s._dsl.level, repr( s ), type( s ), other._dsl.level,
                repr( other ), type( other ) ) )

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

class SendIfcRTL( CallerIfcRTL ):

  def construct( s, Type ):
    super().construct( en=True, rdy=True, MsgType=Type, RetType=None )

  def connect( s, other, parent ):

    # We are doing SendRTL (s) -> [ RecvRTL -> SendCL ] -> RecvCL (other)
    # RecvCL is a callee interface
    if isinstance( other, CalleeIfcCL ):
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


class SendIfcFL( CallerIfcFL ):
  pass

  def connect( s, other, parent ):

    # We are doing SendFL (s) -> [ RecvFL -> SendCL ] -> RecvCL (s)
    # SendCL is a caller interface
    # FIXME direction
    if isinstance( other, CallerIfcCL ) or \
       isinstance( other, CalleeIfcCL ):
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

    elif isinstance( other, SendIfcRTL ):
      m = RecvFL2SendRTL( other.MsgType )

      if hasattr( parent, "RecvFL2SendRTL_count" ):
        count = parent.RecvFL2SendRTL_count
        setattr( parent, "RecvFL2SendRTL_" + str( count ), m )
      else:
        parent.RecvFL2SendRTL_count = 0
        parent.RecvFL2SendRTL_0 = m

      connect_pairs(
        s,      m.recv,
        m.send, other,
      )
      parent.RecvFL2SendRTL_count += 1
      return True

    return False

class RecvIfcFL( CalleeIfcFL ):
  pass

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

    @update_once
    def up_clear():
      if s.send.en: # constraints reverse this
        s.entry = None

    @update
    def up_send_rtl():
      if s.entry is None:
        s.send.en  @= b1( 0 )
      else:
        s.send.en  @= b1( s.send.rdy )
        s.send.msg @= s.entry

    s.add_constraints(
      U( up_clear )   < WR( s.send.en ),
      U( up_clear )   < M( s.recv ),
      U( up_clear )   < M( s.recv.rdy ),
      M( s.recv )     < U( up_send_rtl ),
      M( s.recv.rdy ) < U( up_send_rtl )
    )

  @non_blocking( lambda s : s.entry is None )
  def recv( s, msg ):
    s.entry = clone_deepcopy( msg )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )
    s.send = CallerIfcCL()

    s.sent_msg = None
    s.send_rdy = False

    @update_once
    def up_recv_rtl_rdy():
      s.send_rdy = s.send.rdy() & ~s.reset
      s.recv.rdy @= s.send_rdy

    @update_once
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

    s.send = CallerIfcCL()

    s.add_constraints( M( s.recv ) == M( s.send ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# RecvFL2SendRTL
#-------------------------------------------------------------------------

class RecvFL2SendRTL( Component ):

  def recv( s, msg ):
    while s.entry is not None:
      greenlet.getcurrent().parent.switch(0)
    s.entry = msg

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcFL( method=s.recv )
    s.send = SendIfcRTL( MsgType )

    s.entry = None

    @update
    def up_clear():
      if s.send.en & (s.entry is not None):
        s.entry = None

    @update
    def up_fl_send_rtl():
      if s.send.rdy & (s.entry is not None):
        s.send.en  @= 1
        s.send.msg @= s.entry
      else:
        s.send.en  @= 0

    s.add_constraints( M( s.recv )   < U(up_fl_send_rtl),
                       U( up_clear ) < WR( s.send.en ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )
