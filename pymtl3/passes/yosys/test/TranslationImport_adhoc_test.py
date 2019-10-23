#=========================================================================
# TranslationImport_adhoc_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 15, 2019
"""Test ad-hoc components with yosys-SystemVerilog translation and import."""

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.test.TranslationImport_adhoc_test import (
    test_bit_selection,
    test_comb_assign,
    test_concat,
    test_concat_constants,
    test_concat_mixed,
    test_connect_constant,
    test_for_range_lower_upper,
    test_for_range_lower_upper_step,
    test_for_range_upper,
    test_freevar,
    test_if,
    test_if_bool_op,
    test_if_branches,
    test_if_dangling_else_inner,
    test_if_dangling_else_outter,
    test_if_exp_for,
    test_if_exp_unary_op,
    test_ifc_decls,
    test_interface,
    test_interface_index,
    test_multi_components_ifc_hierarchy_connect,
    test_multi_ifc_decls,
    test_nested_if,
    test_nested_struct,
    test_nested_struct_port,
    test_packed_array,
    test_packed_array_behavioral,
    test_part_selection,
    test_port_bit_selection,
    test_port_const,
    test_port_const_array,
    test_port_part_selection,
    test_port_wire,
    test_port_wire_array_index,
    test_reduce,
    test_seq_assign,
    test_sext,
    test_struct,
    test_struct_const,
    test_struct_const_structural,
    test_struct_packed_array,
    test_struct_port,
    test_subcomp_decl,
    test_subcomponent,
    test_subcomponent_index,
    test_tmpvar,
    test_unpacked_signal_index,
    test_zext,
)
from pymtl3.passes.yosys import ImportPass, TranslationImportPass, TranslationPass
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  try:
    _m.elaborate()
    _m.yosys_translate_import = True
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
    sim.run_test()
  finally:
    try:
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass
