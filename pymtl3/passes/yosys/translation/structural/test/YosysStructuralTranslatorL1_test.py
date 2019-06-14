#=========================================================================
# YosysStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 1 yosys-SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    is_sverilog_reserved,
    test_connect_constant,
    test_port_bit_selection,
    test_port_const,
    test_port_const_array,
    test_port_part_selection,
    test_port_wire,
    test_port_wire_array_index,
)
from pymtl3.passes.yosys.translation.structural.YosysStructuralTranslatorL1 import (
    YosysStructuralTranslatorL1,
)


def local_do_test( m ):
  m.elaborate()
  YosysStructuralTranslatorL1.is_sverilog_reserved = is_sverilog_reserved
  tr = YosysStructuralTranslatorL1( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  assert ports["port_decls"] == m._ref_ports_port_yosys[m]
  assert ports["wire_decls"] == m._ref_ports_wire_yosys[m]
  assert ports["connections"] == m._ref_ports_conn_yosys[m]

  wires = tr.structural.decl_wires[m]
  assert wires == m._ref_wires_yosys[m]

  conns = tr.structural.connections[m]
  assert conns == m._ref_conns_yosys[m]
