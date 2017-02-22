from pymtl import *

from pclib import TestSource
from pclib import TestSink

class Top(UpdateComponent):

  def __init__( s ):

    s.src  = TestSource( [4,3,2,1] )
    s.sink = TestSink  ( ["?","?",7,6,5,4] )

    @s.update
    def up_from_src():
      s.reg0 = s.src.out

    s.reg0  = 0
    s.wire0 = 0

    @s.update
    def upA():
      s.wire0 = s.reg0 + 1

    s.reg1 = 0

    @s.update
    def upB():
      s.reg1 = s.wire0 + 1

    s.reg2 = 0
    
    @s.update
    def upC():
      s.reg2 = s.reg1 + 1

    @s.update
    def up_to_sink():
      s.sink.in_ = s.reg2

    s.add_constraints(
      upA < upB,
      upC < upB,
    )

    s.add_constraints(
      up_from_src < upB,
      upC < up_to_sink,
    )

    up_sink = s.sink.get_update_block("up_sink")

    s.add_constraints(
      up_to_sink < up_sink,
    )

    up_src = s.src.get_update_block("up_src")

    s.add_constraints(
      up_from_src > up_src,
    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " >>> " + \
          "r0=%s > w0=%s > r1=%s > r2=%s" % (s.reg0,s.wire0,s.reg1,s.reg2) + \
           " >>> " + s.sink.line_trace()

A = Top()
A.elaborate()
A.print_schedule()

while not A.done():
  A.cycle()
  print A.line_trace()
