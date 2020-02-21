#=========================================================================
# ImportPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 14, 2019
"""Provide a pass that imports arbitrary SystemVerilog modules."""


from pymtl3.passes.backends.sverilog import ImportConfigs
from pymtl3.passes.backends.sverilog import ImportPass as SVerilogImportPass
from pymtl3.passes.backends.sverilog.errors import SVerilogImportError
from pymtl3.passes.backends.sverilog.util.utility import (
    get_component_unique_name,
    make_indent,
)
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir


class ImportPass( SVerilogImportPass ):

  #-----------------------------------------------------------------------
  # Backend-specific methods
  #-----------------------------------------------------------------------

  def get_backend_name( s ):
    return "yosys"

  def get_config( s, m ):
    return m.config_yosys_import

  def get_translation_namespace( s, m ):
    return m._pass_yosys_translation

  #-------------------------------------------------------------------------
  # Name mangling functions
  #-------------------------------------------------------------------------

  def mangle_vector( s, d, pname, vname, dtype ):
    return [ ( pname, vname, rt.Port( d, dtype ) ) ]

  def mangle_struct( s, d, pname, vname, dtype ):
    ret = []
    for name, field in dtype.get_all_properties().items():
      ret += s.mangle_dtype( d, f"{pname}.{name}", f"{vname}__{name}", field )
    return ret

  def mangle_packed_array( s, d, pname, vname, dtype ):

    def _mangle_packed_array( d, pname, vname, dtype, n_dim ):
      if not n_dim:
        return s.mangle_dtype( d, pname, vname, dtype )
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += _mangle_packed_array( d, f"{pname}[{i}]", f"{vname}__{i}", dtype, n_dim[1:] )
        return ret

    n_dim, sub_dtype = dtype.get_dim_sizes(), dtype.get_sub_dtype()
    return _mangle_packed_array( d, pname, vname, sub_dtype, n_dim )

  def mangle_dtype( s, d, pname, vname, dtype ):
    if isinstance( dtype, rdt.Vector ):
      return s.mangle_vector( d, pname, vname, dtype )
    elif isinstance( dtype, rdt.Struct ):
      return s.mangle_struct( d, pname, vname, dtype )
    elif isinstance( dtype, rdt.PackedArray ):
      return s.mangle_packed_array( d, pname, vname, dtype )

    raise TypeError(f"unrecognized data type {dtype}!")

  def mangle_port( s, pname, vname, port, n_dim ):
    if not n_dim:
      return s.mangle_dtype( port.get_direction(), pname, vname, port.get_dtype() )
    else:
      ret = []
      for i in range( n_dim[0] ):
        ret += s.mangle_port( f"{pname}[{i}]", f"{vname}__{i}", port, n_dim[1:] )
      return ret

  #-------------------------------------------------------------------------
  # PyMTL combinational input and output generation functions
  #-------------------------------------------------------------------------

  def gen_dtype_comb( s, lhs, rhs, dtype, symbols, is_input=False ):

    def _gen_packed_comb( lhs, rhs, dtype, n_dim, symbols ):
      if not n_dim:
        return s.gen_dtype_comb( lhs, rhs, dtype, symbols )
      else:
        ret = []
        for i in range( n_dim[0] ):
          if is_input:
            _lhs = f"{lhs}__{i}"
            _rhs = f"{rhs}[{i}]"
          else:
            _lhs = f"{lhs}[{i}]"
            _rhs = f"{rhs}__{i}"
          ret += _gen_packed_comb( _lhs, _rhs, dtype, n_dim[1:], symbols )
        return ret

    if isinstance( dtype, rdt.Vector ):
      nbits = dtype.get_length()
      if is_input:
        return s._gen_ref_write( lhs, rhs, nbits )
      else:
        return s._gen_ref_read( lhs, rhs, nbits )
    elif isinstance( dtype, rdt.Struct ):
      ret = []
      for name, field in dtype.get_all_properties().items():
        if is_input:
          _lhs = f"{lhs}__{name}"
          _rhs = f"{rhs}.{name}"
        else:
          _lhs = f"{lhs}.{name}"
          _rhs = f"{rhs}__{name}"
        ret += s.gen_dtype_comb( _lhs, _rhs, field )
      return ret
    elif isinstance( dtype, rdt.PackedArray ):
      n_dim = dtype.get_dim_sizes()
      sub_dtype = dtype.get_sub_dtype()
      return _gen_packed_comb( lhs, rhs, sub_dtype, n_dim, is_input )
    else:
      assert False, f"unrecognized data type {dtype}!"

  def gen_port_array_input( s, lhs, rhs, dtype, n_dim, symbols ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, symbols, is_input=True )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = f"{lhs}__{i}"
        _rhs = f"{rhs}[{i}]"
        ret += s.gen_port_array_input( _lhs, _rhs, dtype, n_dim[1:], symbols )
      return ret

  def gen_port_array_output( s, lhs, rhs, dtype, n_dim, symbols ):
    if not n_dim:
      return s.gen_dtype_comb( lhs, rhs, dtype, is_input=False )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _lhs = f"{lhs}[{i}]"
        _rhs = f"{rhs}__{i}"
        ret += s.gen_port_array_output( _lhs, _rhs, dtype, n_dim[1:], symbols )
      return ret
