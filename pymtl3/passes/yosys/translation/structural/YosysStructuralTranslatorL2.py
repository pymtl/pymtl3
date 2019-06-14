#=========================================================================
# YosysStructuralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL2 import (
    SVStructuralTranslatorL2,
)

from .YosysStructuralTranslatorL1 import YosysStructuralTranslatorL1


class YosysStructuralTranslatorL2(
    YosysStructuralTranslatorL1, SVStructuralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # Connection helper method
  #-----------------------------------------------------------------------

  def struct_conn_gen( s, d, pid, wid, idx, dtype ):
    all_properties = dtype.get_all_properties()
    ret = []
    for name, field in all_properties:
      ret += s.dtype_conn_gen( d, pid+"$"+name, wid+"$"+name, idx, field )
    return ret

  def _packed_conn_gen( s, d, pid, wid, idx, n_dim, dtype ):
    if not n_dim:
      return s.dtype_conn_gen( d, pid, wid, idx, dtype )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _pid = pid + "$__{}".format(i)
        _idx = idx + "[{}]".format(i)
        ret += s._packed_conn_gen( d, _pid, wid, _idx, n_dim[1:], dtype )
      return ret

  def packed_conn_gen( s, d, pid, wid, idx, _dtype ):
    n_dim = _dtype.get_dim_sizes()
    dtype = _dtype.get_sub_dtype()
    return s._packed_conn_gen( d, pid, wid, idx, n_dim, dtype )

  def dtype_conn_gen( s, d, pid, wid, idx, dtype ):
    if isinstance( dtype, rdt.Struct ):
      return s.struct_conn_gen( d, pid, wid, idx, dtype )
    elif isinstance( dtype, rdt.PackedArray ):
      return s.packed_conn_gen( d, pid, wid, idx, dtype )
    else:
      return \
        super(YosysStructuralTranslatorL2, s).dtype_conn_gen( d, pid, wid,
                                                             idx, dtype )

  #-----------------------------------------------------------------------
  # Port wire declaration helper method
  #-----------------------------------------------------------------------

  def wire_struct_gen( s, id_, dtype, n_dim ):
    all_properties = dtype.get_all_properties()
    ret = []
    for name, field in all_properties:
      ret += s.wire_dtype_gen( id_+"$"+name, field, n_dim )
    return ret

  def wire_packed_gen( s, id_, _dtype, n_dim ):
    _n_dim = _dtype.get_dim_sizes()
    dtype = _dtype.get_sub_dtype()
    return s.wire_dtype_gen( id_, dtype, n_dim + _n_dim )

  def wire_dtype_gen( s, id_, dtype, n_dim ):
    if isinstance( dtype, rdt.Struct ):
      s.check_decl( id_, "" )
      return s.wire_struct_gen( id_, dtype, n_dim )
    elif isinstance( dtype, rdt.PackedArray ):
      s.check_decl( id_, "" )
      return s.wire_packed_gen( id_, dtype, n_dim )
    else:
      return \
        super(YosysStructuralTranslatorL2, s).wire_dtype_gen(id_, dtype, n_dim )

  #-----------------------------------------------------------------------
  # Port declaration helper methods
  #-----------------------------------------------------------------------

  def _packed_gen( s, d, id_, n_dim, dtype ):
    if not n_dim:
      return s.dtype_gen( d, id_, dtype )
    else:
      ret = []
      for i in range(n_dim[0]):
        ret += s._packed_gen( d, id_+"$__{}".format(i), n_dim[1:], dtype )
      return ret

  def packed_gen( s, d, id_, _dtype ):
    n_dim = _dtype.get_dim_sizes()
    dtype = _dtype.get_sub_dtype()
    return s._packed_gen( d, id_, n_dim, dtype )

  def struct_gen( s, d, id_, dtype ):
    all_properties = dtype.get_all_properties()
    ret = []
    for name, field in all_properties:
      ret += s.dtype_gen( d, id_+"$"+name, field )
    return ret

  def dtype_gen( s, d, id_, dtype ):
    if isinstance( dtype, rdt.Struct ):
      s.check_decl( id_, "" )
      return s.struct_gen(d, id_, dtype)
    elif isinstance( dtype, rdt.PackedArray ):
      s.check_decl( id_, "" )
      return s.packed_gen(d, id_, dtype)
    else:
      return super(YosysStructuralTranslatorL2, s).dtype_gen(d, id_, dtype)

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------
  
  def rtlir_tr_packed_index( s, base_signal, index ):
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_struct_attr( s, base_signal, attr ):
    s.deq[-1]['s_attr'] += "${}"
    s.deq[-1]['attr'].append( attr )
    return '{base_signal}.{attr}'.format( **locals() )
