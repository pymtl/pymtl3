from collections import deque
from pymtl import *
from QueueIfcs import EnqIfc, DeqIfc

class PipeQueue( MethodsConnection ):
  def __init__( s, size=1 ):
    s.queue = deque(maxlen=size)
    s.add_constraints(
      M(s.deq) < M(s.enq), # pipe behavior
    )
    s.enq_ifc = EnqIfc( enq = s.enq, rdy = s.enq_rdy )
    s.deq_ifc = DeqIfc( deq = s.deq, rdy = s.deq_rdy )

  def enq_rdy( s ):    return len(s.queue) < s.queue.maxlen
  def enq( s, v ):     s.queue.appendleft(v)
  def deq_rdy( s ):    return len(s.queue) > 0
  def deq( s ):        return s.queue.pop()
  def line_trace( s ):
    return "Q{:10}".format("".join( [ "[%d]"%x for x in s.queue ]) )

class BypassQueue( MethodsConnection ):
  def __init__( s, size=1 ):
    s.queue = deque(maxlen=size)
    s.add_constraints(
      M(s.enq) < M(s.deq), # bypass behavior
    )
    s.enq_ifc = EnqIfc( enq = s.enq, rdy = s.enq_rdy )
    s.deq_ifc = DeqIfc( deq = s.deq, rdy = s.deq_rdy )

  def enq_rdy( s ):    return len(s.queue) < s.queue.maxlen
  def enq( s, v ):     s.queue.appendleft(v)
  def deq_rdy( s ):    return len(s.queue) > 0
  def deq( s ):        return s.queue.pop()
  def line_trace( s ):
    return "Q{:10}".format("".join( [ "[%d]"%x for x in s.queue ]) )
