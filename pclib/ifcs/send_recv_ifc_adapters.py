#=========================================================================
# Adapters for send/recv interface
#=========================================================================
# CL/RTL adapters for send/recv interface.
#
# Author : Yanghui Ou
#   Date : Mar 07, 2019

from pymtl import *
from pclib.ifcs.SendRecvIfc  import SendIfcRTL, RecvIfcRTL

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2SendRTL( ComponentLevel6 ):

  def construct( s, MsgType ):

    # Interface

    s.send = SendIfcRTL( MsgType )

    s.recv_called = False
    s.msg_to_send = 0  

    @s.update
    def send_msg():
      s.send.en     = Bits1( 1 ) if s.recv_called else Bits1( 0 )
      s.send.msg    = s.msg_to_send
      s.recv_called = False

    s.add_constraints(
      M( s.recv ) < U( send_msg ) 
    )
  
  @method_port( lambda s : s.send.rdy )
  def recv( s, msg ):
    s.msg_to_send = msg
    s.recv_called = True

#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( ComponentLevel6 ):

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )
    s.send = CallerPort()

    @s.update
    def update_rdy():
      s.recv.rdy = Bits1( 1 ) if s.send.rdy() else Bits1( 0 )

    @s.update
    def send_msg():
      if s.recv.en:
        s.send( s.recv.msg )

    s.add_constraints( U( update_rdy ) < M( send_msg ) )
