from pymtl import *

# Register

class Reg(MethodComponent):

  def __init__( s ):
    s.v1 = 0
    s.v2 = 0

    @s.update
    def up_reg():
      s.v2 = s.v1

    s.add_constraints(
      U(up_reg) < M(s.wr),
      M(s.rd)   > U(up_reg),
    )

  def wr( s, v ):
    s.v1 = v

  def rd( s ):
    return s.v2

  def line_trace( s ):
    return "[%4d > %4d]" % (s.v1, s.v2)

# Register with enable signal

class RegEn(MethodComponent):

  def __init__( s ):
    s.v1 = 0
    s.v2 = 0
    s.en = 0

    @s.update
    def up_reg():
      if s.en:
        s.v2 = s.v1

    s.add_constraints(
      U(up_reg) < M(s.wr),
      U(up_reg) < M(s.rd),
      U(up_reg) < M(s.enable),
    )

  def wr( s, v ):
    s.v1 = v

  def rd( s ):
    return s.v2

  def enable( s, en ):
    s.en = en

  def line_trace( s ):
    return "[en:%4d|%4d > %4d]" % (s.en, s.v1, s.v2)
