from pymtl_v3 import *

from TestSource import TestSource
from TestSink   import TestSink

class Top(Updates):

  def __init__( s ):

    s.src  = TestSource( [4,3,2,1] )
    s.sink = TestSink  ( ["?","?","?",7,6,5,4] )

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

    s.set_constraints(
      TS(upA) < TS(upB),
      TS(upC) < TS(upB),
    )

    s.set_constraints(
      TS(up_from_src) < TS(upB),
      TS(upC) < TS(up_to_sink),
    )

    s.set_constraints(
      TS(up_to_sink) < TS(s.sink.up_sink),
    )

    s.set_constraints(
      TS(up_from_src) > TS(s.src.up_src),
    )

  def line_trace( s ):
    return s.src.line_trace() + " >>> " + \
          "r0=%s > w0=%s > r1=%s > r2=%s" % (s.reg0,s.wire0,s.reg1,s.reg2) + \
           ">>>" + s.sink.line_trace()

A = Top()
A.elaborate()
A.print_schedule()

for x in xrange(10):
  A.cycle()
  print A.line_trace()
