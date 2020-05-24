#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Test ad-hoc components with SystemVerilog translation and import."""

import gc
import resource

import pytest

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogPlaceholderPass

from .. import VerilogTranslationImportPass


def _run_case():

  class DUT( Component ):
    def construct( s ):
      s.mem = bytearray(1<<29)
      s.mem[-1]=1
      s.mem[-2]=123
      s.mem[1] =12
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @update
      def upblk():
        s.out @= s.in_ + 1
    def line_trace( s ):
      return f"{s.in_} > {s.out}"

  m = DUT()
  m.elaborate()
  m.set_metadata( VerilogTranslationImportPass.enable, True )
  m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( m )

  m.apply( DefaultPassGroup() )
  m.sim_reset()

  m.in_ @= Bits32(123)
  m.sim_tick()
  assert m.out == 124

  m.finalize()
  gc.collect()
  print("python process memory usage:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024," MB")

def test_verilog_translation_import_adhoc():
  for i in range(10):
    _run_case()
