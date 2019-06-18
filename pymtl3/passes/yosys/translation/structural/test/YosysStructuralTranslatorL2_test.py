#=========================================================================
# YosysStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 2 yosys-SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL2_test import (
    test_nested_struct_port,
    test_packed_array,
    test_struct_const_structural,
    test_struct_packed_array,
    test_struct_port,
)
from pymtl3.passes.yosys.translation.structural.YosysStructuralTranslatorL2 import (
    YosysStructuralTranslatorL2,
)


def local_do_test( m ):
  m.elaborate()
  YosysStructuralTranslatorL2.is_sverilog_reserved = is_sverilog_reserved
  tr = YosysStructuralTranslatorL2( m )
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
