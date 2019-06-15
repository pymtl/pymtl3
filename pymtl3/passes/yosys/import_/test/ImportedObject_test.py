#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.test.ImportedObject_test import test_adder, test_reg
from pymtl3.passes.yosys.import_.ImportPass import ImportPass
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  _m.elaborate()
  _m.yosys_import_path = _m.sverilog_import_path
  ipass = ImportPass()
  m = ipass.get_imported_object( _m )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()
