from pymtl import *

class ImportConstraints( RTLComponent ):
  def construct( s ):
    s.a = InVPort( Bits32 )
    s.b = InVPort( Bits32 )
    s.c = InVPort( Bits32 )

    s.u = OutVPort( Bits32 )
    s.v = OutVPort( Bits32 )

    @s.update
    def c1():
      s.u = s.a + s.b

    @s.update
    def c2():
      s.v = s.c + 1

  def line_trace( s ):
    return 'a={},b={},u=a+b={} | c={},v=c+1={}'.format( s.a, s.b, s.u, s.c, s.v )
