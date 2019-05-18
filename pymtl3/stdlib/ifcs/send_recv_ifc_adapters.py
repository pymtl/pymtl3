"""
========================================================================
Send/RecvIfc adapters
========================================================================
CL/RTL adapters for send/recv interface.

Author : Yanghui Ou
  Date : Mar 07, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

from .GuardedIfc import GuardedCallerIfc, guarded_ifc
from .ifcs_utils import enrdy_to_str
from .SendRecvIfc import RecvIfcRTL, SendIfcRTL

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2SendRTL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.send = SendIfcRTL( MsgType )

    s.recv_called = False
    s.recv_rdy    = False
    s.msg_to_send = 0

    @s.update
    def up_send_rtl():
      s.send.en     = Bits1( 1 ) if s.recv_called else Bits1( 0 )
      s.send.msg    = s.msg_to_send
      s.recv_called = False

    @s.update
    def up_recv_rdy_cl():
      s.recv_rdy    = True if s.send.rdy else False

    s.add_constraints(
      U( up_recv_rdy_cl ) < M( s.recv ),
      U( up_recv_rdy_cl ) < M( s.recv.rdy ),
      M( s.recv.rdy ) < U( up_send_rtl ),
      M( s.recv ) < U( up_send_rtl )
    )

  @guarded_ifc( lambda s : s.recv_rdy )
  def recv( s, msg ):
    s.msg_to_send = msg
    s.recv_called = True

  def line_trace( s ):
    return "{}(){}".format(
      enrdy_to_str( s.msg_to_send, s.recv_called, s.recv_rdy ),
      s.send.line_trace()
    )
#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )
    s.send = GuardedCallerIfc()

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
