from pymtl import *

class Adder( RTLComponent ):

  def construct( s, Type ):
    s.in0 = InVPort( Type )
    s.in1 = InVPort( Type )
    s.out = OutVPort( Type )

    @s.update
    def update_adder(): 
      s.out = s.in0 + s.in1

  def line_trace( s ):
    print 'in0: {}, in1: {}, out: {}'.format( s.in0, s.in1, s.out )
