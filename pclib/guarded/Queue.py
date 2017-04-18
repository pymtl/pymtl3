from collections import deque
from pymtl import *

class PipeQueue( MethodsGuard ):
  def __init__( s, size=1 ):
    s.queue = deque(maxlen=size)
    s.add_constraints(
      M(s.deq) < M(s.enq), # pipe behavior
    )

  @guard(lambda s: len(s.queue) < s.queue.maxlen)
  def enq( s, v ):
    s.queue.appendleft(v)

  @guard(lambda s: len(s.queue) > 0)
  def deq( s ):
    return s.queue.pop()

  def line_trace( s ):
    return "Q{:10}".format("".join( [ "[%d]"%x for x in s.queue ]) )

class BypassQueue( MethodsGuard ):
  def __init__( s, size=1 ):
    s.queue = deque(maxlen=size)
    s.add_constraints(
      M(s.enq) < M(s.deq), # bypass behavior
    )

  @guard(lambda s: len(s.queue) < s.queue.maxlen)
  def enq( s, v ):
    s.queue.appendleft(v)

  @guard(lambda s: len(s.queue) > 0)
  def deq( s ):
    return s.queue.pop()

  def line_trace( s ):
    return "Q{:10}".format("".join( [ "[%d]"%x for x in s.queue ]) )
  def line_trace( s ):
    return "Q{:10}".format("".join( [ "[%d]"%x for x in s.queue ]) )
