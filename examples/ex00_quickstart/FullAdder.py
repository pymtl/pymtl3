#=========================================================================
# FullAdder.py
#=========================================================================

from pymtl3 import *

class FullAdder( Component ):
  def construct( s ):
    s.a    = InPort( Bits1 )
    s.b    = InPort( Bits1 )
    s.cin  = InPort( Bits1 )
    s.sum  = OutPort( Bits1 )
    s.cout = OutPort( Bits1 )
