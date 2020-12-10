#=========================================================================
# RandomDelayQueue.py
#=========================================================================
# This component is non-synthesizable.
# Delay for a random number of cycles for each message enqueued. This
# should create an out-of-order message stream on the dequeue side.
#
# Author : Peitian Pan
# Date   : Nov 11, 2020

from random import seed
from random import randint
from copy import deepcopy

from pymtl3 import *
from pymtl3.stdlib.queues import EnqIfcRTL, DeqIfcRTL

# Toplevel test harness is supposed to call 
# seed(0xfaceb00c)

class RandomDelayQueue( Component ):

  def construct( s, MsgType, salt ):

    # Interfaces

    s.enq = EnqIfcRTL( MsgType )
    s.deq = DeqIfcRTL( MsgType )

    s.msgs_in_flight = []

    s.fire_msg = False
    s.msg_to_fire = None

    # Logic

    @update_once
    def random_delay_q_enq():
      if ~s.reset:
        if s.enq.en & s.enq.rdy:
          delay = randint( 0, 64 )
          msg = deepcopy( s.enq.msg )
          s.msgs_in_flight.append( [ msg, delay ] )

    @update_once
    def random_delay_q_proc():
      if ~s.reset:
        s.fire_msg = False
        s.msg_to_fire = None
        for idx, pairs in enumerate(s.msgs_in_flight):
          msg, delay = pairs[0], pairs[1]
          if delay == 0:
            s.fire_msg = True
            s.msg_to_fire = msg
            s.msgs_in_flight.pop(idx)
            break
          else:
            pairs[1] -=1

    @update
    def random_delay_q_gen_packet():
      if ~s.reset:
        s.deq.rdy @= Bits1(s.fire_msg)
        if s.msg_to_fire:
          s.deq.ret @= s.msg_to_fire
          s.deq.ret.data @= s.msg_to_fire.data + salt
          # s.deq.ret.data   @= s.msg_to_fire.data + salt
          # s.deq.ret.type_  @= s.msg_to_fire.type_
          # s.deq.ret.addr   @= s.msg_to_fire.addr
          # s.deq.ret.opaque @= s.msg_to_fire.opaque
        else:
          s.deq.ret @= MsgType()
          # s.deq.ret.data   @= 0
          # s.deq.ret.type_  @= 0
          # s.deq.ret.addr   @= 0
          # s.deq.ret.opaque @= 0

    # Handshake

    s.enq.rdy //= 1

  def line_trace( s ):
    return f"{s.enq} | {s.deq}"
