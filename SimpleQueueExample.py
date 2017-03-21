from pymtl import *
from pclib.cl import PipeQueue, BypassQueue, EnqIfc

class QueuePlusOne( Methods ):

  def __init__( s ):
    s.recv = EnqIfc()
    s.send = EnqIfc() # to be connected

    s.q     = PipeQueue()
    s.recv |= s.q.enq_ifc

    @s.update
    def up_qp1():
      if s.q.deq_rdy() and s.send.rdy():
        s.send.enq( s.q.deq() + 1 )

  def line_trace( s ):
    return s.q.line_trace() + " +1 "

class Top( Methods ):

  def __init__( s ):

    num_incrs = 5

    s.a = [ QueuePlusOne() for _ in xrange(num_incrs) ]

    for i in xrange(1, num_incrs):
      s.a[i-1].send |= s.a[i].recv

    s.q = BypassQueue()
    s.a[num_incrs - 1].send |= s.q.enq_ifc

    s.src = 0
    @s.update
    def up_src():
      if s.a[0].recv.rdy():
        s.src += 10
        s.a[0].recv.enq( s.src )

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
            " > ".join([ x.line_trace() for x in s.a]) + \
            s.q.line_trace() + " > " + \
           "[%d:%s] sink=%4d >>>" % (s.time, "deq" if s.time == 0 else "   ", s.sink)

A=Top()
A.elaborate()

for cycle in xrange(20):
  A.cycle()
  print A.line_trace()
