from pymtl import *

# N-input Mux

class Mux(MethodsExpl):

  def __init__( s, num_inputs = 2 ):
    s.in_ = [0] * num_inputs
    s.sel = 0
    s.out = 0

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):
    pass
