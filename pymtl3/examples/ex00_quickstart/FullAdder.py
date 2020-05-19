#=========================================================================
# FullAdder.py
#=========================================================================

from pymtl3 import *


class FullAdder( Component ):
  def construct( s ):
    s.a    = InPort()
    s.b    = InPort()
    s.cin  = InPort()
    s.sum  = OutPort()
    s.cout = OutPort()

    @update
    def upblk():
      s.sum  @= s.cin ^ s.a ^ s.b
      s.cout @= ( ( s.a ^ s.b ) & s.cin ) | ( s.a & s.b )
