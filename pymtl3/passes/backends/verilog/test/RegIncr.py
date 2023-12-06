from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogIfcWithSpec

class RegIncr( VerilogIfcWithSpec ):
  def construct( s, nbits=32 ):
    s.in_ = InPort(nbits)
    s.out = OutPort(nbits)

    @update_once
    def upblk():
      s.out @= s.in_ + 1
