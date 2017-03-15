from pymtl import *

# Register

class Reg(UpdatesConnection):

  def __init__( s ):
    s.in_ = 0
    s.out = 0

    @s.update
    def up_reg():
      s.out = s.in_

    s.add_constraints(
      U(up_reg) < WR(s.in_),
      U(up_reg) < RD(s.out),
    )

  def line_trace( s ):
    return "[%6d > %6d]" % (s.in_, s.out)

# Register with enable signal

class RegEn(UpdatesConnection):

  def __init__( s ):
    s.in_ = 0
    s.out = 0
    s.en  = 0

    @s.update
    def up_regen():
      if s.en:
        s.out = s.in_

    s.add_constraints(
      U(up_reg) < WR(s.in_),
      U(up_reg) < WR(s.en),
      U(up_reg) < RD(s.out),
    )

  def line_trace( s ):
    return "[en:%1d|%6d > %6d]" % (s.en, s.in_, s.out)
