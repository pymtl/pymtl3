#=========================================================================
# VStructuralTranslatorL1.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""


from pymtl3.datatypes import Bits
from pymtl3.passes.backends.generic.structural.StructuralTranslatorL1 import (
    StructuralTranslatorL1,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

from ...errors import VerilogPlaceholderError, VerilogReservedKeywordError
from ...util.utility import get_component_unique_name, make_indent, pretty_concat


class VStructuralTranslatorL1( StructuralTranslatorL1 ):

  def check_decl( s, name, msg ):
    if s.is_verilog_reserved( name ):
      raise VerilogReservedKeywordError( name, msg )

  #-----------------------------------------------------------------------
  # Placeholder
  #-----------------------------------------------------------------------

  def rtlir_tr_placeholder_src( s, m ):
    try:
      ph_cfg = m.get_metadata( s._placeholder_pass.placeholder_config )
      if m is s.tr_top:
        # If this placeholder is a top level module, use the wrapper
        # template to support explicit module name.
        if s.tr_cfgs and s.tr_cfgs[m].explicit_module_name:
          module_name = s.tr_cfgs[m].explicit_module_name
        else:
          module_name = ph_cfg.pickled_top_module
          s._mangled_placeholder_top_module_name = module_name

        if module_name == ph_cfg.top_module:
          raise VerilogPlaceholderError(m,
              f"failed to create wrapper for the given object because the same "
              f"name {module_name} is used for both the Verilog top module and "
              f"the wrapper. Please specify a different name through the "
              f"`explicit_module_name` option of TranslationConfigs.")

        # Read the dependency of the placeholder
        nlines     = ph_cfg.pickled_wrapper_nlines
        dependency = '\n'.join( ph_cfg.pickled_source.splitlines()[:-nlines] )

        # Create the placeholder wrapper from the ph_cfg metadata
        wrapper = ph_cfg.pickled_wrapper_template.format(top_module_name=module_name)

        return dependency + wrapper

      else:
        # Otherwise use the pickled placeholder source
        return ph_cfg.pickled_source
    except (AttributeError, OSError):
      # Forgot to apply VerilogPlaceholderPass?
      raise Exception(
                f"error while translating placeholder {m}:\n"
                f"- Did you forget to apply the correct PlaceholderPass(e.g. VerilogPlaceholderPass)?" )

  #-----------------------------------------------------------------------
  # Data types
  #-----------------------------------------------------------------------

  def rtlir_tr_vector_dtype( s, dtype ):
    msb = dtype.get_length() - 1
    return {
      'def'  : '',
      'nbits' : dtype.get_length(),
      'data_type' : 'logic',
      'packed_type' : f'[{msb}:0]',
      'unpacked_type' : '',
      'raw_dtype' : dtype
    }

  def rtlir_tr_unpacked_array_type( s, Type ):
    if Type is None:
      return { 'def' : '', 'unpacked_type' : '', 'n_dim':[] }
    else:
      array_dim = "".join( f"[0:{size-1}]" for size in Type.get_dim_sizes() )
      return {
        'def'  : '',
        'unpacked_type' : array_dim,
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
    direction = Type.get_direction()
    if direction == 'input':
      direction += ' '
    if array_type:
      template = "Note: port {id_} has data type {_dtype}"
    else:
      n_dim = array_type['n_dim']
      template = "Note: {n_dim} array of ports {id_} has data type {_dtype}"
    s.check_decl( id_, template.format( **locals() ) )
    return pretty_concat( direction, dtype['data_type'], dtype['packed_type'],
              id_, array_type['unpacked_type'] )

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
    return pretty_concat( dtype['data_type'], dtype['packed_type'],
              id_, array_type['unpacked_type'], ';' )

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
      return f"'{{ {', '.join(ret)} }}"

  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
    _dtype = Type.get_dtype()
    if array_type:
      template = "Note: constant {id_} has data type {_dtype}"
    else:
      n_dim = array_type['n_dim']
      template = "Note: {n_dim} array of constants {id_} has data type {_dtype}"
    s.check_decl( id_, template.format( **locals() ) )
    _dtype = pretty_concat(dtype['data_type'], dtype['packed_type'], id_, array_type['unpacked_type'])
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

  def rtlir_tr_bit_selection( s, base_signal, index, status ):
    # Bit selection
    return s._rtlir_tr_process_unpacked(
              f'{base_signal}[{index}]',
              f'{base_signal}{{}}[{index}]',
              status, ('status', 'unpacked') )

  def rtlir_tr_part_selection( s, base_signal, start, stop, status ):
    # Part selection
    return s._rtlir_tr_process_unpacked(
              f'{base_signal}[{stop-1}:{start}]',
              f'{base_signal}{{}}[{stop-1}:{start}]',
              status, ('status', 'unpacked') )

  def rtlir_tr_port_array_index( s, base_signal, index, status ):
    return s._rtlir_tr_process_unpacked(
              f'{base_signal}[{index}]',
              f'{base_signal}{{}}[{index}]',
              status, ('status', 'unpacked') )

  def rtlir_tr_wire_array_index( s, base_signal, index, status ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_const_array_index( s, base_signal, index, status ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_current_comp_attr( s, base_signal, attr, status ):
    return f'{attr}'

  def rtlir_tr_current_comp( s, comp_id, comp_rtype, status ):
    return ''

  def _rtlir_tr_process_unpacked( s, signal, signal_tplt, status, enable ):
    if (status in ('reader', 'writer') and 'status' in enable) or \
       (s._rtlir_tr_unpacked_q and 'unpacked' in enable):
      ret = signal_tplt.format(''.join(
                [f'[{i}]' for i in list(s._rtlir_tr_unpacked_q)]))
      s._rtlir_tr_unpacked_q.clear()
      return ret
    else:
      return signal

  #-----------------------------------------------------------------------
  # Miscs
  #-----------------------------------------------------------------------

  def rtlir_tr_var_id( s, var_id ):
    return var_id.replace( '[', '__' ).replace( ']', '' )

  def _literal_number( s, nbits, value ):
    return f"{nbits}'d{int(value)}"

  def rtlir_tr_literal_number( s, nbits, value ):
    return s._literal_number( nbits, value )

  def rtlir_tr_component_unique_name( s, c_rtype ):
    return get_component_unique_name( c_rtype )
