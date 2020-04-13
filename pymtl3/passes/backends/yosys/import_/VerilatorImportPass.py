#=========================================================================
# VerilatorImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 14, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""


from pymtl3.passes.backends.verilog import VerilatorImportPass as VerilogImportPass
from pymtl3.passes.backends.verilog.errors import VerilogImportError
from pymtl3.passes.backends.verilog.util.utility import (
    get_component_unique_name,
    make_indent,
)
from pymtl3.passes.backends.yosys.util.utility import gen_mapped_ports
from pymtl3.passes.BasePass import BasePass


class VerilatorImportPass( VerilogImportPass ):

  #-----------------------------------------------------------------------
  # Backend-specific methods
  #-----------------------------------------------------------------------

  def get_backend_name( s ):
    return "yosys"

  def get_config( s, m ):
    return m.config_yosys_import

  def get_config_name( s ):
    return "config_yosys_import"

  def get_translation_namespace( s, m ):
    return m._pass_yosys_translation

  def get_gen_mapped_port( s ):
    return gen_mapped_ports

  #-----------------------------------------------------------------------
  # Customize assignments in the Python wrapper
  #-----------------------------------------------------------------------

  def gen_port_array_input( s, lhs, rhs, pnames, dtype, index, n_dim, symbols ):
    if not n_dim:
      return s.gen_port_input( lhs, rhs, pnames, dtype, symbols )
    else:
      set_comb, structs = [], []
      for idx in range( n_dim[0] ):
        _lhs = f"{lhs}__{i}"
        if index == 0:
          _rhs = f"{rhs}[{idx}]"
          _index = index-1
        else:
          _rhs = rhs
          _index = index
        _set_comb, _structs = s.gen_port_array_input( _lhs, _rhs, pnames, dtype, _index, n_dim[1:], symbols )
        set_comb += _set_comb
        structs  += _structs
      return set_comb, structs

  def gen_port_array_output( s, lhs, pnames, rhs, dtype, index, n_dim, symbols ):
    if not n_dim:
      return s.gen_port_output( lhs, pnames, rhs, dtype, symbols )
    else:
      set_comb, structs = [], []
      for idx in range( n_dim[0] ):
        if index == 0:
          _lhs = f"{lhs}[{idx}]"
          _index = index-1
        else:
          _lhs = lhs
          _index = index
        _rhs = f"{rhs}__{i}"
        _set_comb, _structs = s.gen_port_array_output( _lhs, pnames, _rhs, dtype, _index, n_dim[1:], symbols )
        set_comb += _set_comb
        structs  += _structs
      return set_comb, structs
