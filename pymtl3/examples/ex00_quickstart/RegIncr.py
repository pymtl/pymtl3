#=========================================================================
# RegIncr.py
#=========================================================================

from pymtl3 import *


class RegIncr( Component ):
  def construct( s, nbits ):
    s.in_ = InPort( nbits )
    s.out = OutPort( nbits )

    s.reg_out = Wire( nbits )

    @update_ff
    def upblk_ff():
      if s.reset:
        s.reg_out <<= 0
      else:
        s.reg_out <<= s.in_

    @update
    def upblk_comb():
      s.out @= s.reg_out + 1
