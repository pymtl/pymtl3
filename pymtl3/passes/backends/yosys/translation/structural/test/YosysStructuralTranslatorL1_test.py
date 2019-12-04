#=========================================================================
# YosysStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 1 yosys-SystemVerilog structural translator."""

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
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
  wires = tr.structural.decl_wires[m]
  conns = tr.structural.connections[m]
  check_eq( ports["port_decls"], m._ref_ports_port_yosys[m] )
  check_eq( ports["wire_decls"], m._ref_ports_wire_yosys[m] )
  check_eq( ports["connections"], m._ref_ports_conn_yosys[m] )
  check_eq( wires, m._ref_wires_yosys[m] )
  check_eq( conns, m._ref_conns_yosys[m] )
