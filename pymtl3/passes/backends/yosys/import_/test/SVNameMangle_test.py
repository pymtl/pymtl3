#=========================================================================
# SVNameMangle_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 15, 2019
"""Test the SystemVerilog name mangling."""

from pymtl3.passes.backends.sverilog.import_.test.SVNameMangle_test import (
    test_interface,
    test_interface_array,
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
  result = ipass.gen_packed_ports( rtype )
  assert result == m._ref_ports_yosys
