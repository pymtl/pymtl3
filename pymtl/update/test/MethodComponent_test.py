from pymtl import *

class Wire(MethodComponent):

  def __init__( s ):
    s.v = 0

    s.add_constraints(
      M(s.wr) < M(s.rd),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class Reg(MethodComponent):

  def __init__( s ):
    s.v1 = 0
    s.v2 = 0

    @s.update
    def up_reg():
      s.v2 = s.v1

    s.add_constraints(
      up_reg  < M(s.wr),
      M(s.rd) > up_reg,
    )

  def wr( s, v ):
    s.v1 = v

  def rd( s ):
    return s.v2

  def line_trace( s ):
    return "[%d > %d]" % (s.v1, s.v2)

class RegWire(MethodComponent):

  def __init__( s ):
    s.v = 0

    s.add_constraints(
      M(s.rd) < M(s.wr),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class Top(MethodComponent):

  def __init__( s ):
    s.inc = 0

    s.in_ = Wire()

    @s.update
    def up_src():
      s.inc += 1
      s.in_.wr( s.inc )

    s.reg0 = Reg()

    @s.update
    def up_plus_one_to_reg0():
      s.reg0.wr( s.in_.rd() + 1 )

    s.reg1 = Reg()

    @s.update
    def up_reg0_to_reg1():
      s.reg1.wr( s.reg0.rd() )

    s.out = 0
    @s.update
    def up_sink():
      s.out = s.reg1.rd()

  def line_trace( s ):
    return  s.in_.line_trace() + " >>> " + s.reg0.line_trace() + \
            " > " + s.reg1.line_trace() +\
            " >>> " + "out=%d" % s.out

def test_2regs():
  A = Top()
  A.elaborate()
  A.print_schedule()

  for x in xrange(1000000):
    A.cycle()
    # print A.line_trace()
