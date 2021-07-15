from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from .ifcs import RecvIfcRTL, SendIfcRTL

class RecvQueueAdapter( Component ):

  @non_blocking( lambda s: s.entry is not None )
  def deq( s ):
    ret = s.entry
    s.entry = None
    return ret

  def construct( s, Type ):
    s.recv = RecvIfcRTL( Type )
    s.entry = None

    @update_once
    def up_recv_rdy():
      s.recv.rdy @= (s.entry is None)

    @update_once
    def up_recv_msg():
      if (s.entry is None) & s.recv.val:
        s.entry = clone_deepcopy( s.recv.msg )

    s.add_constraints( M( s.deq )     < U( up_recv_rdy ), # deq before recv in a cycle -- pipe behavior
                       M( s.deq.rdy ) < U( up_recv_rdy ),
                       U( up_recv_rdy ) < U( up_recv_msg ) )


class SendQueueAdapter( Component ):

  @non_blocking( lambda s: s.entry is None )
  def enq( s, msg ):
    s.entry = clone_deepcopy( msg )

  def construct( s, Type ):
    s.send = SendIfcRTL( Type )

    s.entry = None
    s.sent  = Wire()

    @update_once
    def up_send():
      if s.entry is None:
        s.send.val @= 0
      else:
        s.send.val @= 1
        s.send.msg @= s.entry

    @update_ff
    def up_sent():
      s.sent <<= s.send.val & s.send.rdy

    @update_once
    def up_clear():
      if s.sent: # constraints reverse this
        s.entry = None

    s.add_constraints(
      U( up_clear )  < M( s.enq ),
      U( up_clear )  < M( s.enq.rdy ),
      M( s.enq )     < U( up_send ),
      M( s.enq.rdy ) < U( up_send )
    )
