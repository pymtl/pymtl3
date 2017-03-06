from pymtl import *
from ports import Port

# N-input Mux

class Mux(InterfaceComponent):

  def __init__( s, num_inputs = 2 ):
    s.in_ = [ Port(int) for _ in xrange(num_inputs) ]
    s.sel = Port(int)
    s.out = Port(int)

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel.rd() ].rd()

  def line_trace( s ):
    return "[in%1d]" % (s.sel.rd() )

class Subtractor(InterfaceComponent):

  def __init__( s ):
    s.in0 = Port(int)
    s.in1 = Port(int)
    s.out = Port(int)

    @s.update
    def up_subtract():
      s.out.wr( s.in0.rd() - s.in1.rd() )

  def line_trace( s ):
    return "[%4s-%4s=%4s]" % (s.in0.line_trace(), \
                              s.in1.line_trace(), \
                              s.out.line_trace() )
