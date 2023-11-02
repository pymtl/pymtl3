#=========================================================================
# TranslationImport_xdist_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 11th, 2023
"""Test if Verilated models can be simulated in parallel."""

import os, pytest, multiprocessing

from pymtl3.datatypes import Bits32
from pymtl3.passes import DefaultPassGroup
from pymtl3.passes.backends.verilog import VerilogPlaceholderPass, VerilogTranslationImportPass

from ..testcases import Bits32VRegComp

if 'CI' in os.environ:
  MAX_XDIST_TEST_INSTS = 10
else:
  MAX_XDIST_TEST_INSTS = 500

@pytest.mark.parametrize(
  'test_id', list(range(MAX_XDIST_TEST_INSTS))
)
def test_verilator_co_simulation( test_id ):
  n_cycles = 100

  m = Bits32VRegComp()
  m.elaborate()
  m.set_metadata( VerilogTranslationImportPass.enable, True )
  m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( m )
  m.apply( DefaultPassGroup() )

  m.sim_reset()

  for i in range(n_cycles):
    m.d @= Bits32(test_id + i)
    m.sim_tick()
    assert m.q == Bits32(test_id + i)

  m.finalize()
