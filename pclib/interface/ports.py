from pymtl import *

class Port(InterfaceComponent):

  def __init__( s, type_ ):
    s.value = type_()

    s.add_constraints(
      M(s.wr) < M(s.rd)
    )

  def wr( s, v ):
    s.value = v

  def rd( s ):
    return s.value

  def line_trace( s ):
    return "%d" % s.value
