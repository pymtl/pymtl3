from os.path import dirname
from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogIfcWithSpec, VerilogPlaceholderPass
from pymtl3.stdlib.test_utils import run_spec_test

def test_verilog_model_with_spec():

  class VAdder( VerilogIfcWithSpec ):
    def construct( s ):
      s.a = InPort(Bits32)
      s.b = InPort(Bits32)
      s.sum = OutPort(Bits32)

      s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VAdder.v' )

      @update_once
      def upblk():
        s.sum @= s.a + s.b

  test = run_spec_test( VAdder )
  test()
