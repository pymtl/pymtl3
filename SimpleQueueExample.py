from pymtl import *
from collections import deque


class Queue( Methods ):
  def __init__( s ):
    s.queue = deque(maxlen=1)
    s.add_constraints(
      M(s.deq) < M(s.enq), # pipe behavior
      # M(s.enq) < M(s.deq), # bypass behavior
    )

  def enq_rdy( s ):    return len(s.queue) < s.queue.maxlen
  def enq( s, v ):     s.queue.append(v)
  def deq_rdy( s ):    return len(s.queue) > 0
  def deq( s ):        return s.queue.pop()
  def line_trace( s ):
    if len(s.queue) == 0: return "Q[   ]"
    return "Q[%3d]" % s.queue[0]

class QueuePlusOne( Methods ):

  def __init__( s ):
    s.q         = Queue()
    s.recv      = MethodPort( s.q.enq )
    s.recv_rdy  = MethodPort()
    s.recv_rdy |= s.q.enq_rdy

    s.send      = MethodPort()
    s.send_rdy  = MethodPort()

    @s.update
    def up_qp1():
      if s.q.deq_rdy() and s.send_rdy():
        s.send( s.q.deq() + 1 )

  def line_trace( s ):
    return s.q.line_trace() + " +1 "

class Top( Methods ):

  def __init__( s ):

    s.a = [ QueuePlusOne() for _ in xrange(2) ]

    s.a[0].send     |= s.a[1].recv
    s.a[0].send_rdy |= s.a[1].recv_rdy

    s.q = Queue()
    s.a[1].send     |= s.q.enq
    s.a[1].send_rdy |= s.q.enq_rdy

    s.src = 0
    @s.update
    def up_src():

      if s.a[0].recv_rdy():
        s.src += 10
        s.a[0].recv( s.src )

    s.time = 0
    s.sink = 0

    @s.update
    def up_sink():
      s.time = (s.time + 1) % 1
      if s.time == 0: # emulate some back pressure
        if s.q.deq_rdy():
          s.sink = s.q.deq()

  def line_trace( s ):
    return "src=%4d >>> " % s.src + \
            s.a[0].line_trace() + " > " + \
            s.a[1].line_trace() + " > " + \
            s.q.line_trace() + " > " + \
           "[%d:%s] sink=%4d >>>" % (s.time, "deq" if s.time == 0 else "   ", s.sink)

A=Top()
A.elaborate()

for cycle in xrange(10):
  A.cycle()
  print A.line_trace()
