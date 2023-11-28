from os.path import dirname

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogIfcWithSpec, VerilogPlaceholderPass
from pymtl3.stdlib.test_utils import run_spec_test

def test_vadder():

  class VAdder( VerilogIfcWithSpec ):
    def construct( s ):
      s.a = InPort(Bits32)
      s.b = InPort(Bits32)
      s.sum = OutPort(Bits32)

      s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VAdder.v' )

      @update_once
      def upblk():
        s.sum @= s.a + s.b

  run_spec_test( VAdder )

def test_vreg_incr():

  class VRegIncr( VerilogIfcWithSpec ):
    def construct( s ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)

      s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VRegIncr.v' )

      @update_once
      def upblk():
        s.out @= s.in_ + 1

  run_spec_test( VRegIncr )
