"""
========================================================================
ComponentLevel4_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 25, 2017
"""
from __future__ import absolute_import, division, print_function

from collections import deque

from pymtl3.datatypes import *
from pymtl3.dsl import *

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )
  print(A._dsl.schedule)

  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print(A.line_trace())
    T += 1

class SimpleReg( ComponentLevel4 ):

  def construct( s ):
    s.read  = CalleePort( s.rd )
    s.write = CalleePort( s.wr )

    s.v = 0

    s.add_constraints(
      M(s.rd) < M(s.wr),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class SimpleWire( ComponentLevel4 ):

  def construct( s ):
    s.read  = CalleePort( s.rd )
    s.write = CalleePort( s.wr )

    s.v = 0

    s.add_constraints(
      M(s.rd) > M(s.wr),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class BaseQueue( ComponentLevel4 ):
  def construct( s, size ):
    s.queue = deque( maxlen=size )

    s.enq     = CalleePort( s.enq_ )
    s.enq_rdy = CalleePort( s.enq_rdy_ )

    s.deq     = CalleePort( s.deq_ )
    s.deq_rdy = CalleePort( s.deq_rdy_ )

  def enq_rdy_( s ): return len(s.queue) < s.queue.maxlen
  def enq_( s, v ):  s.queue.appendleft(v)
  def deq_rdy_( s ): return len(s.queue) > 0
  def deq_( s ):     return s.queue.pop()

class PipeQueue( BaseQueue ):

  def construct( s, size ):
    super( PipeQueue, s ).construct( size )
    s.add_constraints(
      M(s.deq_    ) < M(s.enq_    ), # pipe behavior
      M(s.deq_rdy_) < M(s.enq_rdy_),
    )

  def line_trace( s ):
    return "[P] {:5}".format(",".join( [ str(x) for x in s.queue ]) )

class BypassQueue( BaseQueue ):

  def construct( s, size ):
    super( BypassQueue, s ).construct( size )
    s.add_constraints(
      M(s.enq_    ) < M(s.deq_    ), # bypass behavior
      M(s.enq_rdy_) < M(s.deq_rdy_),
    )

  def line_trace( s ):
    return "[B] {:5}".format(",".join( [ str(x) for x in s.queue ]) )

def test_2regs():

  class Top( ComponentLevel4 ):

    def construct( s ):
      s.in_ = Wire(int)

      @s.update
      def up_src():
        s.in_ += 1

      s.reg0 = SimpleReg()

      @s.update
      def up_plus_one_to_reg0():
        s.reg0.write( s.in_ + 1 )

      s.reg1 = SimpleReg()

      @s.update
      def up_reg0_to_reg1():
        s.reg1.write( s.reg0.read() + 1)

      s.out = Wire(int)
      @s.update
      def up_sink():
        s.out = s.reg1.read()

    def done( s ):
      return s.in_ >= 5

    def line_trace( s ):
      return  "in=%d" % s.in_ + " >>> " + s.reg0.line_trace() + \
              " > " + s.reg1.line_trace() +\
              " >>> " + "out=%d" % s.out


  _test_model( Top )

def test_bypass_queue():

  class Top( ComponentLevel4 ):

    def construct( s ):
      s.in_ = 0

      @s.update
      def up_src():
        s.in_ += 1

      s.q = BypassQueue( 1 )

      @s.update
      def up_plus_one_to_q():
        if s.q.enq_rdy():
          s.q.enq( s.in_ + 1 )

      s.out = 0
      @s.update
      def up_sink():
        s.out = 'X'
        #  if s.in_ % 3 == 0:
        if s.q.deq_rdy():
          s.out = s.q.deq()

    def done( s ):
      return s.in_ >= 5

    def line_trace( s ):
      return  "in=" + str(s.in_) + " >>> " + s.q.line_trace() + \
              " >>> " + "out=" + str(s.out)


  _test_model( Top )

def test_pipe_queue():

  class Top( ComponentLevel4 ):

    def construct( s ):
      s.in_ = 0

      @s.update
      def up_src():
        s.in_ += 1

      s.q = PipeQueue( 1 )

      @s.update
      def up_plus_one_to_q():
        if s.q.enq_rdy():
          s.q.enq( s.in_ + 1 )

      s.out = 0
      @s.update
      def up_sink():
        s.out = 'X'
        #  if s.in_ % 3 == 0:
        if s.q.deq_rdy():
          s.out = s.q.deq()

    def done( s ):
      return s.in_ >= 5

    def line_trace( s ):
      return  "in=" + str(s.in_) + " >>> " + s.q.line_trace() + \
              " >>> " + "out=" + str(s.out)


  _test_model( Top )
