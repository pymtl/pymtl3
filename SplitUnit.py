from pymtl import *
from pclib.cl import PipeQueue, BypassQueue

class Msg( object ):
  def __init__( s ):
    s.id  = int
    s.val = int

  def __call__( s ):
    msg     = Msg()
    msg.id  = 0
    msg.val = 0
    return msg

  def mk_msg( s, x, y ):
    msg = Msg()
    msg.id  = x
    msg.val = y
    return msg

  def __str__( s ):
    return "{:3d}:{:3d}".format( s.id, s.val )

  def __repr__( s ):
    return "{:3d}:{:3d}".format( s.id, s.val )

class SplitUnit( MethodsGuard ):
  def __init__( s ):
    s.RR = 0
    s.send     = [ MethodPort() for _ in xrange(2) ]
    s.send_rdy = [ MethodPort() for _ in xrange(2) ]

  def recv( s, msg ):
    s.send[ s.RR ]( msg )
    s.RR = (s.RR + 1) % 2

  def recv_rdy( s ):
    return s.send_rdy[s.RR]()

class Top( MethodsGuard ):
  def __init__( s ):

    s.split = SplitUnit()
    s.qs    = [ PipeQueue( size=2 ) for _ in xrange(2) ]

    for i in xrange(2):
      s.qs[i].enq     |= s.split.send[i]
      s.qs[i].enq_rdy |= s.split.send_rdy[i]

    s.ts = 0

    s.msg_type = Msg()
    import random

    seq  = range(16)
    random.seed(0x1)
    random.shuffle( seq )
    s.msgs = [ s.msg_type.mk_msg( i, i<<1 ) for i in seq ]

    @s.update
    def up_src_send():
      if s.ts < len(s.msgs) and s.split.recv_rdy():
        s.split.recv( s.msgs[ s.ts ] )
        s.ts += 1

    s.time = 0

    @s.update
    def up_sink_recv():
      s.time = (s.time + 1) % 1
      for i in xrange(2):
        if s.time == 0 and s.qs[i].deq_rdy():
          print "Q #%d: %s" % (i, s.qs[i].deq() ),
        else:
          print "Q #%d:        " % i,

      print

top = Top()
top.elaborate()
top.print_schedule()

for i in xrange(20):
  top.cycle()
