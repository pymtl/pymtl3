#=========================================================================
# VNameMangle_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 15, 2019
"""Test the SystemVerilog name mangling."""

from pymtl3.passes.backends.verilog.import_.test.VNameMangle_test import (
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
from pymtl3.passes.backends.yosys.util.utility import gen_mapped_ports
from pymtl3.passes.rtlir.util.test_utility import do_test


def local_do_test( m ):
  m.elaborate()
  result = gen_mapped_ports( m, {} )
  assert result == m._ref_ports_yosys
