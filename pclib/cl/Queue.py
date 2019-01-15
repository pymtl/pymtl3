from collections import deque
from pymtl import *

class BaseQueue( ComponentLevel5 ):
  def construct( s, size ):
    s.queue = deque( maxlen=size )

    s.enq     = CalleePort( s.enq_ )
    s.enq_rdy = CalleePort( s.enq_rdy_ )

    s.deq     = CalleePort( s.deq_ )
    s.deq_rdy = CalleePort( s.deq_rdy_ )
    s.peek    = CalleePort( s.peek_ )

  def enq_rdy_( s ): return len(s.queue) < s.queue.maxlen
  def enq_( s, v ):  s.queue.appendleft(v)
  def deq_rdy_( s ): return len(s.queue) > 0
  def deq_( s ):     return s.queue.pop()
  def peek_( s ):    return s.queue[-1]

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
