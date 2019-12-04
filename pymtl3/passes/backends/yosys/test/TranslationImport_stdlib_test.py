#=========================================================================
# TranslationImport_stdlib_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 15, 2019
"""Test stdlib RTL components with SystemVerilog translation and import.

We reuse all the test cases from stdlib test files. To achieve this I
overwrite the original reference to the test function used in stdlib test
files and add my own test function (the `run_test`s). However we need
to make sure the orignal reference is not lost and is restored after
finishing each test (no matter it fails or passes).
"""

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.test.TranslationImport_stdlib_test import (
    test_2entry_normal_Bits,
    test_3entry_normal_Bits,
    test_arbiter_rr_arb_4,
    test_arbiter_rr_arb_en_4,
    test_bypass_Bits,
    test_crossbar3,
    test_encoder_5_directed,
    test_normal_Bits,
    test_pipe_Bits,
)
from pymtl3.passes.yosys import TranslationImportPass
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  try:
    _m.elaborate()
    # Mark component `_m` as to be translated and imported
    _m.yosys_translate_import = True
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
    sim.run_test()
  finally:
    try:
      # Explicitly finalize imported component to avoid shared lib name aliasing
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass
