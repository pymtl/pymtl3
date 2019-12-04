#=========================================================================
# SVStructuralTranslatorL1.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3.datatypes import Bits
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.sverilog.errors import SVerilogReservedKeywordError
from pymtl3.passes.sverilog.util.utility import get_component_unique_name, make_indent
from pymtl3.passes.translator.structural.StructuralTranslatorL1 import (
    StructuralTranslatorL1,
)


class SVStructuralTranslatorL1( StructuralTranslatorL1 ):

  def check_decl( s, name, msg ):
    if s.is_sverilog_reserved( name ):
      raise SVerilogReservedKeywordError( name, msg )

  #-----------------------------------------------------------------------
  # Data types
  #-----------------------------------------------------------------------

  def rtlir_tr_vector_dtype( s, dtype ):
    msb = dtype.get_length() - 1
    return {
      'def'  : '',
      'nbits' : dtype.get_length(),
      'const_decl' : f'[{msb}:0] {{id_}}',
      'decl' : f'logic [{msb}:0] {{id_}}',
      'raw_dtype' : dtype
    }

  def rtlir_tr_unpacked_array_type( s, Type ):
    if Type is None:
      return { 'def' : '', 'decl' : '', 'n_dim':[] }
    else:
      array_dim = "".join( f"[0:{size-1}]" for size in Type.get_dim_sizes() )
      return {
        'def'  : '',
        'decl' : ' ' + array_dim,
        'n_dim' : Type.get_dim_sizes()
      }

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_port_decls( s, port_decls ):
    make_indent( port_decls, 1 )
    return ',\n'.join( port_decls )

  def rtlir_tr_port_decl( s, id_, Type, array_type, dtype ):
    _dtype = Type.get_dtype()
    if array_type:
      template = "Note: port {id_} has data type {_dtype}"
    else:
      n_dim = array_type['n_dim']
      template = "Note: {n_dim} array of ports {id_} has data type {_dtype}"
    s.check_decl( id_, template.format( **locals() ) )
    return Type.get_direction() + ' ' + \
           dtype['decl'].format( **locals() ) + array_type['decl']

  def rtlir_tr_wire_decls( s, wire_decls ):
    make_indent( wire_decls, 1 )
    return '\n'.join( wire_decls )

  def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
    _dtype = Type.get_dtype()
    if array_type:
      template = "Note: wire {id_} has data type {_dtype}"
    else:
      n_dim = array_type['n_dim']
      template = "Note: {n_dim} array of wires {id_} has data type {_dtype}"
    s.check_decl( id_, template.format( **locals() ) )
    return dtype['decl'].format( **locals() ) + array_type['decl'] + ';'

  def rtlir_tr_const_decls( s, const_decls ):
    make_indent( const_decls, 1 )
    return '\n'.join( const_decls )

  def gen_array_param( s, n_dim, dtype, array ):
    if not n_dim:
      if isinstance( dtype, rdt.Vector ):
        return s._literal_number( dtype.get_length(), array )
      else:
        assert False, f'{array} is not an integer or a BitStruct!'
    else:
      ret = []
      for _idx, idx in enumerate( range( n_dim[0] ) ):
        ret.append( s.gen_array_param( n_dim[1:], dtype, array[idx] ) )
      cat_str = ", ".join( ret )
      return f"'{{ {cat_str} }}"

  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
    _dtype = Type.get_dtype()
    if array_type:
      template = "Note: constant {id_} has data type {_dtype}"
    else:
      n_dim = array_type['n_dim']
      template = "Note: {n_dim} array of constants {id_} has data type {_dtype}"
    s.check_decl( id_, template.format( **locals() ) )
    _dtype = dtype['const_decl'].format( **locals() ) + array_type['decl']
    _value = s.gen_array_param( array_type['n_dim'], dtype['raw_dtype'], value )

    return f'localparam {_dtype} = {_value};'

  #-----------------------------------------------------------------------
  # Connections
  #-----------------------------------------------------------------------

  def rtlir_tr_connections( s, connections ):
    make_indent( connections, 1 )
    return '\n'.join( connections )

  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    return f'assign {rd_signal} = {wr_signal};'

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_bit_selection( s, base_signal, index ):
    # Bit selection
    return f'{base_signal}[{index}]'

  def rtlir_tr_part_selection( s, base_signal, start, stop ):
    # Part selection
    _stop = stop-1
    return f'{base_signal}[{_stop}:{start}]'

  def rtlir_tr_port_array_index( s, base_signal, index ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_wire_array_index( s, base_signal, index ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_const_array_index( s, base_signal, index ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_current_comp_attr( s, base_signal, attr ):
    return f'{attr}'

  def rtlir_tr_current_comp( s, comp_id, comp_rtype ):
    return ''

  #-----------------------------------------------------------------------
  # Miscs
  #-----------------------------------------------------------------------

  def rtlir_tr_var_id( s, var_id ):
    return var_id.replace( '[', '__' ).replace( ']', '' )

  def _literal_number( s, nbits, value ):
    value = int( value )
    return f"{nbits}'d{value}"

  def rtlir_tr_literal_number( s, nbits, value ):
    return s._literal_number( nbits, value )

  def rtlir_tr_component_unique_name( s, c_rtype ):
    return get_component_unique_name( c_rtype )
