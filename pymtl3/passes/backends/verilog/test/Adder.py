from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogIfcWithSpec

class Adder( VerilogIfcWithSpec ):
  def construct( s, nbits=32 ):
    s.a = InPort(nbits)
    s.b = InPort(nbits)
    s.sum = OutPort(nbits)

    @update_once
    def upblk():
      s.sum @= s.a + s.b
