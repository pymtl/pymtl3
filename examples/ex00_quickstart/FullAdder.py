#=========================================================================
# FullAdder.py
#=========================================================================

from pymtl3 import *

class FullAdder( Component ):
  def construct( s ):
    s.a    = InPort( 1 )
    s.b    = InPort( 1 )
    s.cin  = InPort( 1 )
    s.sum  = OutPort( 1 )
    s.cout = OutPort( 1 )

    @update
    def upblk():
      s.sum  @= s.cin ^ s.a ^ s.b
      s.cout @= ( ( s.a ^ s.b ) & s.cin ) | ( s.a & s.b )
