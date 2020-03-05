#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Test ad-hoc components with SystemVerilog translation and import."""

import pytest

from pymtl3.passes.backends.verilog import VerilogPlaceholderPass
from pymtl3.passes.rtlir.util.test_utility import get_parameter
from pymtl3.stdlib.test import TestVectorSimulator

from .. import TranslationImportPass
from ..testcases import (
    CasePlaceholderTranslationRegIncr,
    CasePlaceholderTranslationVReg,
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
  try:
    _m = case.DUT()
    _m.elaborate()
    _m.verilog_translate_import = True
    _m.apply( VerilogPlaceholderPass() )
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, case.TEST_VECTOR, case.TV_IN, case.TV_OUT )
    sim.run_test()
  finally:
    try:
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass

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
          ]
)
def test_verilog_translation_import_adhoc( case ):
  run_test( case )
