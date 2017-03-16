from pymtl import *

# N-input Mux

class Mux(UpdatesConnection):

  def __init__( s, ninputs ):
    s.in_ = [ ValuePort(int) for _ in xrange(ninputs) ]
    s.sel = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

    for x in s.in_:
      s.add_constraints(
        WR(x) < U(up_mux),
      )

    s.add_constraints(
      WR(s.sel) < U(up_mux),
      U(up_mux) < RD(s.out),
    )

  def line_trace( s ):  pass
