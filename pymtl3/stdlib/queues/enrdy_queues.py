"""
========================================================================
enrdy_queues.py
========================================================================
This file contains queues with EnRdy (send/recv) interface.

Author : Shunning Jiang
Date   : Mar 9, 2018
"""

from pymtl3 import *
from pymtl3.stdlib.basic_rtl import Mux, Reg, RegEn, RegRst
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL


class PipeQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = RecvIfcRTL( Type )
    s.deq = SendIfcRTL( Type )

    s.buffer = m = RegEn( Type )
    m.en  //= s.enq.en
    m.in_ //= s.enq.msg
    m.out //= s.deq.msg

    s.full = Reg( Bits1 )

    @update
    def up_pipeq_use_deq_rdy():
      s.deq.en  @=  s.full.out & s.deq.rdy
      s.enq.rdy @= ~s.full.out | s.deq.rdy

    @update
    def up_pipeq_full():
      s.full.in_ @= s.enq.en | (s.full.out & ~s.deq.rdy )

  def line_trace( s ):
    return s.buffer.line_trace()

class BypassQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = RecvIfcRTL( Type )
    s.deq = SendIfcRTL( Type )

    s.buffer = RegEn( Type )
    s.buffer.in_ //= s.enq.msg

    s.full = RegRst( Bits1, reset_value = 0 )

    s.byp_mux = m = Mux( Type, 2 )
    m.out    //= s.deq.msg
    m.in_[0] //= s.enq.msg
    m.in_[1] //= s.buffer.out
    m.sel    //= s.full.out # full -- buffer.out, empty -- bypass

    @update
    def up_bypq_set_enq_rdy():
      s.enq.rdy @= ~s.full.out

    @update
    def up_bypq_use_enq_en():
      s.deq.en    @= (s.enq.en | s.full.out) & s.deq.rdy
      s.buffer.en @=  s.enq.en & ~s.deq.en
      s.full.in_  @= (s.enq.en | s.full.out) & ~s.deq.en

  def line_trace( s ):
    return s.buffer.line_trace()

class BypassQueue2RTL( Component ):

  def construct( s, MsgType, queue_size=2 ):
    assert queue_size == 2
    s.enq = RecvIfcRTL( MsgType )
    s.deq = SendIfcRTL( MsgType )
    s.q1 = BypassQueue1RTL( MsgType )
    s.q2 = BypassQueue1RTL( MsgType )

    s.enq    //= s.q1.enq
    s.q1.deq //= s.q2.enq
    s.q2.deq //= s.deq

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.q1.deq, s.deq )

class NormalQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = RecvIfcRTL( Type )
    s.deq = SendIfcRTL( Type )

    # Now since enq.en depends on enq.rdy, enq.en == 1 actually means
    # we will enq some stuff
    s.buffer = m = RegEn( Type )
    m.en  //= s.enq.en
    m.in_ //= s.enq.msg
    m.out //= s.deq.msg
    s.full = Reg( Bits1 )

    @update
    def up_normq_set_enq_rdy():
      s.enq.rdy @= ~s.full.out

    @update
    def up_normq_full():
      # When the bufferf is full and deq side is ready, we enable deq
      s.deq.en @= s.full.out & s.deq.rdy

      # not full and valid enq, or no deque and enq, or no deque and already full
      s.full.in_ @= (~s.full.out & s.enq.en) | \
                    (~s.deq.rdy & s.enq.en)  | \
                    (~s.deq.rdy & s.full.out)


  def line_trace( s ):
    return s.buffer.line_trace()
