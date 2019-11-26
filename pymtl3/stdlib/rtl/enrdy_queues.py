"""
========================================================================
enrdy_queues.py
========================================================================
This file contains queues with EnRdy (send/recv) interface.

Author : Shunning Jiang
Date   : Mar 9, 2018
"""

from typing import TypeVar, Generic

from pymtl3 import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl import Mux, Reg, RegEn, RegRst


class PipeQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = RecvIfcRTL( Type )
    s.deq = SendIfcRTL( Type )

    s.buffer  = RegEn( Type )( en = s.enq.en, in_ = s.enq.msg, out = s.deq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_pipeq_use_deq_rdy():
      s.deq.en  =  s.full.out & s.deq.rdy
      s.enq.rdy = ~s.full.out | s.deq.rdy

    @s.update
    def up_pipeq_full():
      s.full.in_ = s.enq.en | (s.full.out & ~s.deq.rdy )

  def line_trace( s ):
    return s.buffer.line_trace()

T_BpsQ1RTLDataType = TypeVar('T_BpsQ1RTLDataType')

class BypassQueue1RTL( Component, Generic[T_BpsQ1RTLDataType] ):

  def construct( s ):
    s.enq = RecvIfcRTL[T_BpsQ1RTLDataType]()
    s.deq = SendIfcRTL[T_BpsQ1RTLDataType]()

    s.buffer = RegEn[T_BpsQ1RTLDataType]()( in_ = s.enq.msg )

    s.full = RegRst[Bits1]( reset_value = 0 )

    s.byp_mux = Mux[T_BpsQ1RTLDataType, Bits1]( 2 )(
      out = s.deq.msg,
      in_ = { 0: s.enq.msg,
              1: s.buffer.out, },
      sel = s.full.out, # full -- buffer.out, empty -- bypass
    )

    @s.update
    def up_bypq_set_enq_rdy():
      s.enq.rdy = ~s.full.out

    @s.update
    def up_bypq_use_enq_en():
      s.deq.en   = (s.enq.en | s.full.out) & s.deq.rdy
      s.buffer.en   =  s.enq.en & ~s.deq.en
      s.full.in_ = (s.enq.en | s.full.out) & ~s.deq.en

  def line_trace( s ):
    return s.buffer.line_trace()

T_BpsQ2RTLDataType = TypeVar('T_BpsQ2RTLDataType')

class BypassQueue2RTL( Component, Generic[T_BpsQ2RTLDataType] ):

  def construct( s ):
    s.enq = RecvIfcRTL[T_BpsQ2RTLDataType]()
    s.deq = SendIfcRTL[T_BpsQ2RTLDataType]()
    s.q1 = BypassQueue1RTL[T_BpsQ2RTLDataType]()( enq = s.enq )
    s.q2 = BypassQueue1RTL[T_BpsQ2RTLDataType]()( enq = s.q1.deq, deq = s.deq )

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.q1.deq, s.deq )

class NormalQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = RecvIfcRTL( Type )
    s.deq = SendIfcRTL( Type )

    # Now since enq.en depends on enq.rdy, enq.en == 1 actually means
    # we will enq some stuff
    s.buffer  = RegEn( Type )( en = s.enq.en, in_ = s.enq.msg, out = s.deq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_normq_set_enq_rdy():
      s.enq.rdy = ~s.full.out

    @s.update
    def up_normq_full():
      # When the bufferf is full and deq side is ready, we enable deq
      s.deq.en = s.full.out & s.deq.rdy

      # not full and valid enq, or no deque and enq, or no deque and already full
      s.full.in_ = (~s.full.out & s.enq.en) | \
                   (~s.deq.rdy & s.enq.en)  | \
                   (~s.deq.rdy & s.full.out)


  def line_trace( s ):
    return s.buffer.line_trace()
