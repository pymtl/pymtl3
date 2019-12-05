#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

from pymtl3.passes.backends.sverilog.import_.test.ImportedObject_test import (
    test_adder,
    test_reg,
)
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test import TestVectorSimulator

from ..ImportPass import ImportPass


def local_do_test( _m ):
  _m.elaborate()
  _m.config_yosys_import = _m.config_sverilog_import
  ipass = ImportPass()
  _m.config_yosys_import.fill_missing( _m )
  m = ipass.get_imported_object( _m )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()
