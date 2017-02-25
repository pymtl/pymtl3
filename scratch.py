from pymtl import *

from pclib import TestSource
from pclib import TestSink

class Top(UpdateComponent):

  def __init__( s ):

    s.src  = TestSource( [4,3,2,1] )
    s.sink = TestSink  ( ["?","?",6,5,4,3] )

    @s.update
    def up_from_src():
      s.reg1 = s.src.out

    up_src = s.src.get_update_block("up_src")

    s.reg1  = 0
    s.wire1 = 0

    @s.update
    def upA():
      s.wire1 = s.reg1 + 1

    # up_from_src models an edge
    s.add_constraints(
      up_from_src < up_src,
      up_from_src < upA,
    )

    s.reg2  = 0
    
    @s.update
    def upB():
      s.reg2 = s.wire1 + 1

    @s.update
    def up_to_sink():
      s.sink.in_ = s.reg2

    # upC models an edge
    s.add_constraints(
      upB < upA,
      upB < up_to_sink,
    )

    up_sink = s.sink.get_update_block("up_sink")

    s.add_constraints(
      up_to_sink < up_sink,
    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " >>> " + \
          "r1=%s > w1=%s > r2=%s" % (s.reg1,s.wire1,s.reg2) + \
           " >>> " + s.sink.line_trace()

A = Top()
A.elaborate()
A.print_schedule()

while not A.done():
  A.cycle()
  print A.line_trace()
