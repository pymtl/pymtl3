from pymtl import *
from ports import Port

# Register

class Reg(InterfaceComponent):

  def __init__( s ):
    s.in_ = Port(int)
    s.out = Port(int)

    @s.update
    def up_reg():
      s.out.wr( s.in_.rd() )

    s.add_constraints(
      U(up_reg) < M(s.in_.wr),
      # U(up_reg) < M(s.out.rd), don't need this as s.out has (wr < rd)
    )

  def line_trace( s ):
    return "[%4s > %4s]" % (s.in_.line_trace(), s.out.line_trace())

# Register with enable signal

class RegEn(InterfaceComponent):

  def __init__( s ):
    s.in_ = Port(int)
    s.out = Port(int)
    s.en  = Port(bool)

    @s.update
    def up_reg():
      if s.en.rd():
        s.out.wr( s.in_.rd() )

    s.add_constraints(
      U(up_reg) < M(s.en.wr),
      U(up_reg) < M(s.in_.wr),
      # U(up_reg) < M(s.out.rd),
    )

  def line_trace( s ):
    return "[en:%5s|%4s > %4s]" % (s.en.line_trace(), s.in_.line_trace(), s.out.line_trace())
