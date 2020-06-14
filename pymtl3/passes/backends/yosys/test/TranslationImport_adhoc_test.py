#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 15, 2019
"""Test ad-hoc components with yosys-SystemVerilog translation and import."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import get_parameter
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ..translation.behavioral.test.YosysBehavioralTranslatorL1_test import (
    test_yosys_behavioral_L1,
)
from ..translation.behavioral.test.YosysBehavioralTranslatorL2_test import (
    test_yosys_behavioral_L2,
)
from ..translation.behavioral.test.YosysBehavioralTranslatorL3_test import (
    test_yosys_behavioral_L3,
)
from ..translation.behavioral.test.YosysBehavioralTranslatorL4_test import (
    test_yosys_behavioral_L4,
)
from ..translation.behavioral.test.YosysBehavioralTranslatorL5_test import (
    test_yosys_behavioral_L5,
)
from ..translation.structural.test.YosysStructuralTranslatorL1_test import (
    test_yosys_structural_L1,
)
from ..translation.structural.test.YosysStructuralTranslatorL2_test import (
    test_yosys_structural_L2,
)
from ..translation.structural.test.YosysStructuralTranslatorL3_test import (
    test_yosys_structural_L3,
)
from ..translation.structural.test.YosysStructuralTranslatorL4_test import (
    test_yosys_structural_L4,
)
from ..YosysTranslationImportPass import YosysTranslationImportPass

XFAILED_TESTS = [
    # incoherent translation result of Yosys backend
    # the translated design is correct after minor transformation
    # in logic synthesis, but verilator simulation is incorrect
    'CaseConnectLiteralStructComp',
]

def run_test( case ):
  _m = case.DUT()
  _m.elaborate()
  _m.set_metadata( YosysTranslationImportPass.enable, True )
  m = YosysTranslationImportPass()( _m )
  sim = TestVectorSimulator( m, case.TV, case.TV_IN, case.TV_OUT )
  sim.run_test()

@pytest.mark.parametrize(
  'case', list(filter(lambda x: x.__name__ not in XFAILED_TESTS,
          get_parameter('case', test_yosys_behavioral_L1) + \
          get_parameter('case', test_yosys_behavioral_L2) + \
          get_parameter('case', test_yosys_behavioral_L3) + \
          get_parameter('case', test_yosys_behavioral_L4) + \
          get_parameter('case', test_yosys_behavioral_L5) + \
          get_parameter('case', test_yosys_structural_L1) + \
          get_parameter('case', test_yosys_structural_L2) + \
          get_parameter('case', test_yosys_structural_L3) + \
          get_parameter('case', test_yosys_structural_L4) ) )
)
def test_yosys_translation_import_adhoc( case ):
  run_test( case )
