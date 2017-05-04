from collections import deque
from pymtl import *
from pclib.ifcs import EnqIfcCL, DeqIfcCL

class BaseQueue( MethodsConnection ):
  def __init__( s, Type, size ):
    s.queue = deque( maxlen=size )

    s.enq = EnqIfcCL( Type )
    s.enq.enq |= s.enq_
    s.enq.rdy |= s.enq_rdy_

    s.deq = DeqIfcCL( Type )
    s.deq.deq |= s.deq_
    s.deq.rdy |= s.deq_rdy_

  def enq_rdy_( s ): return len(s.queue) < s.queue.maxlen
  def enq_( s, v ):  s.queue.appendleft(v)
  def deq_rdy_( s ): return len(s.queue) > 0
  def deq_( s ):     return s.queue.pop()

class PipeQueue( BaseQueue ):

  def __init__( s, Type, size ):
    super( PipeQueue, s ).__init__( Type, size )
    s.add_constraints(
      M(s.deq_    ) < M(s.enq_    ), # pipe behavior
      M(s.deq_rdy_) < M(s.enq_rdy_),
    )

  def line_trace( s ):
    return "[P] {:5}".format(",".join( [ str(x) for x in s.queue ]) )

class BypassQueue( BaseQueue ):

  def __init__( s, Type, size):
    super( BypassQueue, s ).__init__( Type, size )
    s.add_constraints(
      M(s.enq    ) < M(s.deq    ), # bypass behavior
      M(s.enq_rdy) < M(s.deq_rdy),
    )

  def line_trace( s ):
    return "[B] {:5}".format(",".join( [ str(x) for x in s.queue ]) )
