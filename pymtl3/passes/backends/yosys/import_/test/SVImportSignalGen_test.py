#=========================================================================
# SVImportSignalGen.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 1, 2019
"""Test the SystemVerilog signal generation of imported component."""

from pymtl3.passes.backends.sverilog.import_.test.SVImportSignalGen_test import (
    test_interface,
    test_interface_array,
    test_interface_parameter,
    test_interface_parameter_long_vector,
    test_nested_interface,
    test_nested_interface_port_array,
    test_nested_struct,
    test_packed_array_port_array,
    test_port_2d_array,
    test_port_array,
    test_port_single,
    test_struct_port_array,
    test_struct_port_single,
)
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test

from ..ImportPass import ImportPass


def local_do_test( m ):
  m.elaborate()
  rtype = rt.get_component_ifc_rtlir( m )
  ipass = ImportPass()
  symbols, decls, conns = ipass.gen_signal_decl_py( rtype )
  assert conns == m._ref_conns_yosys
