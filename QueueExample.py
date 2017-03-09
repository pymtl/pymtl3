from pymtl import *
from collections import deque

class EnqIfc(Interface):
  def enq_rdy( s ): pass
  def enq( s, v ):  pass

class DeqIfc(Interface):
  def deq_rdy( s ): pass
  def deq( s, v ):  pass

class Queue( MethodComponent ):
  def __init__( s ):
    s.enqifc = EnqIfc( s.enq, s.enq_rdy )
    s.deqifc = DeqIfc( s.deq, s.deq_rdy )

    s.queue = deque(maxlen=1)

  def enq_rdy( s ): return len(s.queue) < s.queue.maxlen
  def enq( s, v ):  s.queue.append(v)
  def deq_rdy( s ): return len(s.queue) > 0
  def deq( s ):     return s.queue.pop()

class QueuePlusOne( MethodComponent ):

  def __init__( s ):
    s.recv  = EnqIfc()
    s.send  = EnqIfc()
    s.q     = Queue()
    s.recv |= s.q.enqifc

    @s.update
    def up_qp1():
      if s.q.deq_rdy() and s.send.enq_rdy():
        s.send.enq( s.q.deq() )

class Top( MethodComponent ):

  def __init__( s ):

    s.a = QueuePlusOne()
    s.b = QueuePlusOne()
    s.a.send |= s.b.recv

    s.q = Queue()
    s.b.send |= s.q.enqifc

    s.src = 0
    @s.update
    def up_src():
      if s.a.recv.enq_rdy():
        s.src += 1
        s.a.recv.enq( s.src )

    s.time = 0
    s.sink = 0
    @s.update
    def up_sink():
      s.time = s.time + 1
      if s.time % 3 == 0: # emulate some back pressure
        if s.q.deq_rdy():
          s.sink = s.q.deq()

  def line_trace( s ):
    return "%4d > ... > %4d" % (s.src,s.sink)

A=Top()
A.elaborate()

for cycle in xrange(10):
  A.cycle()
  print A.line_trace()
  
