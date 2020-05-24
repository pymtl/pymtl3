#=========================================================================
# YosysStructuralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog structural translator."""

from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.translation.structural.VStructuralTranslatorL2 import (
    VStructuralTranslatorL2,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt

from .YosysStructuralTranslatorL1 import YosysStructuralTranslatorL1


class YosysStructuralTranslatorL2(
    YosysStructuralTranslatorL1, VStructuralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # Connection helper method
  #-----------------------------------------------------------------------

  def vec_conn_vector_gen( s, d, c_nbits, pid, wid, idx, dtype ):
    nbits = dtype.get_length()
    assert c_nbits - nbits >= 0
    msb, lsb = c_nbits-1, c_nbits-nbits
    return [ {
      "direction" : d,
      "pid" : pid,
      "wid" : wid,
      "idx" : idx + f"[{msb}:{lsb}]",
      "present" : True
    } ]

  def vec_conn_struct_gen( s, d, c_nbits, pid, wid, idx, dtype ):
    ret = []
    for name, field in dtype.get_all_properties().items():
      ret += s.vec_conn_dtype_gen( d, c_nbits, pid+"__"+name, wid, idx, field )
      c_nbits -= field.get_length()
    return ret

  def vec_conn_packed_gen( s, d, c_nbits, pid, wid, idx, _dtype ):

    def _packed_gen( d, c_nbits, pid, wid, idx, n_dim, p_nbits, dtype ):
      if not n_dim:
        return s.vec_conn_dtype_gen( d, c_nbits, pid, wid, idx, dtype )
      else:
        ret = []
        dec_nbits = p_nbits // n_dim[0]
        for i in reversed( range( n_dim[0]) ):
          ret += \
            _packed_gen(d, c_nbits, pid+"__"+str(i), wid, idx, n_dim[1:], dec_nbits, dtype)
          c_nbits -= dec_nbits
          assert c_nbits >= 0
        return ret

    p_n_dim = _dtype.get_dim_sizes()
    p_nbits = _dtype.get_length()
    dtype = _dtype.get_sub_dtype()
    return _packed_gen( d, c_nbits, pid, wid, idx, p_n_dim, p_nbits, dtype )

  def vec_conn_dtype_gen( s, d, c_nbits, pid, wid, idx, dtype ):
    if isinstance( dtype, rdt.Vector ):
      return s.vec_conn_vector_gen( d, c_nbits, pid, wid, idx, dtype )
    elif isinstance( dtype, rdt.Struct ):
      return s.vec_conn_struct_gen( d, c_nbits, pid, wid, idx, dtype )
    elif isinstance( dtype, rdt.PackedArray ):
      return s.vec_conn_packed_gen( d, c_nbits, pid, wid, idx, dtype )

    raise TypeError( f"unrecognized data type {dtype}!" )

  def struct_conn_gen( s, d, pid, wid, idx, dtype ):
    ret = []
    for name, field in dtype.get_all_properties().items():
      ret += s.dtype_conn_gen( d, pid+"__"+name, wid+"__"+name, idx, field )
    cur_nbits = dtype.get_length()
    for name, field in dtype.get_all_properties().items():
      ret += s.vec_conn_dtype_gen( d, cur_nbits, pid+"__"+name, wid, idx, field )
      cur_nbits -= field.get_length()
    assert cur_nbits == 0
    return ret

  def _packed_conn_gen( s, d, pid, wid, idx, n_dim, dtype ):
    if not n_dim:
      return s.dtype_conn_gen( d, pid, wid, idx, dtype )
    else:
      ret = []
      for i in range( n_dim[0] ):
        _pid = f"{pid}__{i}"
        _idx = f"{idx}[{i}]"
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
      return super().dtype_conn_gen( d, pid, wid, idx, dtype )

  #-----------------------------------------------------------------------
  # Port wire declaration helper method
  #-----------------------------------------------------------------------

  def wire_struct_gen( s, id_, dtype, n_dim ):
    ret = []
    # Generate wire for each field
    for name, field in dtype.get_all_properties().items():
      ret += s.wire_dtype_gen( id_+"__"+name, field, n_dim )
    # Generate a long vector for this struct signal
    ret.append( {
      "msb" : dtype.get_length()-1,
      "id_" : id_,
      "n_dim" : n_dim,
      "present" : True
    } )
    return ret

  def wire_packed_gen( s, id_, _dtype, n_dim ):
    _n_dim = _dtype.get_dim_sizes()
    dtype = _dtype.get_sub_dtype()
    ret = s.wire_dtype_gen( id_, dtype, n_dim + _n_dim )
    # Rigth now don't generate dedicated wire for the whole packed array -
    # we generate an unpacked array to group together all signals. Users
    # should access each element of the array instead of manipulating
    # this array as a whole.
    # ret.append( {
      # "msb" : _dtype.get_length()-1,
      # "id_" : id_,
      # "n_dim" : n_dim,
      # "present" : True
    # } )
    return ret

  def wire_dtype_gen( s, id_, dtype, n_dim ):
    if isinstance( dtype, rdt.Struct ):
      s.check_decl( id_, "" )
      return s.wire_struct_gen( id_, dtype, n_dim )
    elif isinstance( dtype, rdt.PackedArray ):
      s.check_decl( id_, "" )
      return s.wire_packed_gen( id_, dtype, n_dim )
    else:
      return \
        super().wire_dtype_gen(id_, dtype, n_dim )

  #-----------------------------------------------------------------------
  # Port declaration helper methods
  #-----------------------------------------------------------------------

  def _packed_gen( s, d, id_, n_dim, dtype ):
    if not n_dim:
      return s.dtype_gen( d, id_, dtype )
    else:
      ret = []
      for i in range(n_dim[0]):
        ret += s._packed_gen( d, f"{id_}__{i}", n_dim[1:], dtype )
      return ret

  def packed_gen( s, d, id_, _dtype ):
    n_dim = _dtype.get_dim_sizes()
    dtype = _dtype.get_sub_dtype()
    return s._packed_gen( d, id_, n_dim, dtype )

  def struct_gen( s, d, id_, dtype ):
    ret = []
    for name, field in dtype.get_all_properties().items():
      ret += s.dtype_gen( d, id_+"__"+name, field )
    return ret

  def dtype_gen( s, d, id_, dtype ):
    if isinstance( dtype, rdt.Struct ):
      s.check_decl( id_, "" )
      return s.struct_gen(d, id_, dtype)
    elif isinstance( dtype, rdt.PackedArray ):
      s.check_decl( id_, "" )
      return s.packed_gen(d, id_, dtype)
    else:
      return super().dtype_gen(d, id_, dtype)

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_packed_index( s, base_signal, index, status ):
    s.deq[-1]['s_index'] += "[{}]"
    s.deq[-1]['index'].append( int(index) )
    return f'{base_signal}[{index}]'

  def rtlir_tr_struct_attr( s, base_signal, attr, status ):
    s.deq[-1]['s_attr'] += "__{}"
    s.deq[-1]['attr'].append( attr )
    return f'{base_signal}.{attr}'

  def rtlir_tr_struct_instance( s, dtype, struct, first_called = True ):
    def _gen_packed_array( dtype, n_dim, array ):
      if not n_dim:
        if isinstance( dtype, rdt.Vector ):
          s_attr = s.rtlir_tr_literal_number( dtype.nbits, array, False )
          return {'attr':[], 'index':[], 's_attr':s_attr, 's_index':""}
        elif isinstance( dtype, rdt.Struct ):
          s_attr = s.rtlir_tr_struct_instance( dtype, array, False )
          return {'attr':[], 'index':[], 's_attr':s_attr, 's_index':""}
        else:
          assert False, f"unrecognized data type {dtype}!"
      else:
        ret = []
        for i in reversed( range( n_dim[0]) ):
          _ret = _gen_packed_array( dtype, n_dim[1:], array[i] )
          ret.append( _ret["s_attr"] )
        if n_dim[0] > 1:
          cat_str = "{{ " + ", ".join( ret ) + " }}"
        else:
          cat_str = ", ".join( ret )
        return {'attr':[], 'index':[], 's_attr':cat_str, 's_index':""}
    fields = []
    for name, Type in dtype.get_all_properties().items():
      field = getattr( struct, name )
      if isinstance( Type, rdt.Vector ):
        _field = s.rtlir_tr_literal_number( Type.nbits, field, False )
      elif isinstance( Type, rdt.Struct ):
        _field = s.rtlir_tr_struct_instance( Type, field, False )
      elif isinstance( Type, rdt.PackedArray ):
        n_dim = Type.get_dim_sizes()
        sub_dtype = Type.get_sub_dtype()
        _field = _gen_packed_array( sub_dtype, n_dim, field )['s_attr']
      else:
        assert False, f"unrecognized data type {Type}!"
      fields.append( _field )
    if len( fields ) == 1:
      struct_str = fields[0]
    else:
      struct_str = "{{ " + ", ".join( fields ) + " }}"
    if first_called:
      s.deq.append( {'attr':[], 'index':[], 's_attr':struct_str, 's_index':""} )
    return struct_str
