#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Test ad-hoc components with SystemVerilog translation and import."""

import pytest

from pymtl3.datatypes import Bits16, Bits32, bitstruct, concat
from pymtl3.dsl import Component, InPort, Interface, OutPort, update
from pymtl3.passes.backends.verilog import VerilogPlaceholderPass
from pymtl3.passes.rtlir.util.test_utility import get_parameter
from pymtl3.stdlib.test_utils import TestVectorSimulator

from .. import VerilogTranslationImportPass
from ..testcases import (
    CaseChildExplicitModuleName,
    CaseMultiPlaceholderImport,
    CasePlaceholderTranslationRegIncr,
    CasePlaceholderTranslationVReg,
    CaseVIncludePopulation,
    CaseVLibsTranslation,
)
from ..translation.behavioral.test.VBehavioralTranslatorL1_test import (
    test_verilog_behavioral_L1,
)
from ..translation.behavioral.test.VBehavioralTranslatorL2_test import (
    test_verilog_behavioral_L2,
)
from ..translation.behavioral.test.VBehavioralTranslatorL3_test import (
    test_verilog_behavioral_L3,
)
from ..translation.behavioral.test.VBehavioralTranslatorL4_test import (
    test_verilog_behavioral_L4,
)
from ..translation.behavioral.test.VBehavioralTranslatorL5_test import (
    test_verilog_behavioral_L5,
)
from ..translation.structural.test.VStructuralTranslatorL1_test import (
    test_verilog_structural_L1,
)
from ..translation.structural.test.VStructuralTranslatorL2_test import (
    test_verilog_structural_L2,
)
from ..translation.structural.test.VStructuralTranslatorL3_test import (
    test_verilog_structural_L3,
)
from ..translation.structural.test.VStructuralTranslatorL4_test import (
    test_verilog_structural_L4,
)


def run_test( case ):
  _m = case.DUT()
  _m.elaborate()
  _m.set_metadata( VerilogTranslationImportPass.enable, True )
  _m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( _m )
  sim = TestVectorSimulator( m, case.TV, case.TV_IN, case.TV_OUT )
  sim.run_test()

@pytest.mark.parametrize(
  'case', get_parameter('case', test_verilog_behavioral_L1) + \
          get_parameter('case', test_verilog_behavioral_L2) + \
          get_parameter('case', test_verilog_behavioral_L3) + \
          get_parameter('case', test_verilog_behavioral_L4) + \
          get_parameter('case', test_verilog_behavioral_L5) + \
          get_parameter('case', test_verilog_structural_L1) + \
          get_parameter('case', test_verilog_structural_L2) + \
          get_parameter('case', test_verilog_structural_L3) + \
          get_parameter('case', test_verilog_structural_L4) + [
            CasePlaceholderTranslationVReg,
            CasePlaceholderTranslationRegIncr,
            CaseVIncludePopulation,
            CaseVLibsTranslation,
            CaseChildExplicitModuleName,
          ]
)
def test_verilog_translation_import_adhoc( case ):
  run_test( case )

def test_pymtl_top_multi_placeholder():
  case = CaseMultiPlaceholderImport
  m = case.DUT()
  m.elaborate()
  m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( m )
  sim = TestVectorSimulator( m, case.TV, case.TV_IN, case.TV_OUT )
  sim.run_test()

def test_bitstruct_same_name_different_fields():
  class A:
    @bitstruct
    class A:
      a: Bits32

  class B:
    @bitstruct
    class A:
      a: Bits16

  class InIfc( Interface ):
    def construct( s, Type ):
      s.in_ = InPort( Type )

  class OutIfc( Interface ):
    def construct( s, Type ):
      s.out = OutPort( Type )

  class DUT( Component ):
    def construct( s ):
      s.in1 = InIfc(A.A)
      s.in2 = InIfc(B.A)
      s.out2 = OutPort(Bits16)

      s.out2 //= s.in2.in_.a

  class TMP( Component ):
    def construct( s ):
      s.out = OutPort(B.A)
      @update
      def drive():
        s.out @= 0

  class Top( Component ):
    def construct( s ):
      s.dut = DUT()
      s.tmp = TMP()
      s.tmp.out //= s.dut.in2.in_

  m = Top()
  m.elaborate()
  m.dut.set_metadata( VerilogTranslationImportPass.enable, True )
  m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( m )
  m.dut.finalize()
