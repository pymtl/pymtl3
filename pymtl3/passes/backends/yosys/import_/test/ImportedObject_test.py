#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

from pymtl3.passes.backends.verilog import TranslationImportPass, VerilogPlaceholderPass
from pymtl3.passes.backends.verilog.import_.test.ImportedObject_test import (
    test_adder,
    test_normal_queue,
    test_normal_queue_params,
    test_reg,
    test_reg_external_trace,
    test_reg_incomplete_portmap,
    test_vl_uninit,
)
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  _m.elaborate()
  _m.yosys_translate_import = True
  _m.apply( VerilogPlaceholderPass() )
  m = TranslationImportPass()( _m )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()
