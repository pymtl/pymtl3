#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Test ad-hoc components with SystemVerilog translation and import."""

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog import TranslationImportPass
from pymtl3.stdlib.test import TestVectorSimulator

from ..translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    test_bit_selection,
    test_comb_assign,
    test_concat,
    test_concat_constants,
    test_concat_mixed,
    test_freevar,
    test_part_selection,
    test_seq_assign,
    test_sext,
    test_unpacked_signal_index,
    test_zext,
)
from ..translation.behavioral.test.SVBehavioralTranslatorL2_test import (
    test_for_range_lower_upper,
    test_for_range_lower_upper_step,
    test_for_range_upper,
    test_if,
    test_if_bool_op,
    test_if_branches,
    test_if_dangling_else_inner,
    test_if_dangling_else_outter,
    test_if_exp_for,
    test_if_exp_unary_op,
    test_nested_if,
    test_reduce,
    test_tmpvar,
)
from ..translation.behavioral.test.SVBehavioralTranslatorL3_test import (
    test_nested_struct,
    test_packed_array_behavioral,
    test_struct,
    test_struct_const,
)
from ..translation.behavioral.test.SVBehavioralTranslatorL4_test import (
    test_interface,
    test_interface_index,
)
from ..translation.behavioral.test.SVBehavioralTranslatorL5_test import (
    test_subcomponent,
    test_subcomponent_index,
)
from ..translation.structural.test.SVStructuralTranslatorL1_test import (
    test_connect_constant,
    test_port_bit_selection,
    test_port_const,
    test_port_const_array,
    test_port_part_selection,
    test_port_wire,
    test_port_wire_array_index,
)
from ..translation.structural.test.SVStructuralTranslatorL2_test import (
    test_nested_struct_port,
    test_packed_array,
    test_struct_const_structural,
    test_struct_packed_array,
    test_struct_port,
)
from ..translation.structural.test.SVStructuralTranslatorL3_test import (
    test_ifc_decls,
    test_multi_ifc_decls,
)
from ..translation.structural.test.SVStructuralTranslatorL4_test import (
    test_multi_components_ifc_hierarchy_connect,
    test_subcomp_decl,
)


def local_do_test( _m ):
  try:
    _m.elaborate()
    _m.sverilog_translate_import = True
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
    sim.run_test()
  finally:
    try:
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass
