#=========================================================================
# SVStructuralTranslatorL4.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3 import Placeholder
from pymtl3.passes.backends.generic.structural.StructuralTranslatorL4 import (
    StructuralTranslatorL4,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

from ...util.utility import make_indent
from .SVStructuralTranslatorL3 import SVStructuralTranslatorL3


class SVStructuralTranslatorL4(
    SVStructuralTranslatorL3, StructuralTranslatorL4 ):

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_subcomp_port_decls( s, _port_decls ):
    port_defs = [x['def'] for x in _port_decls]
    port_decls = [x['decl'] for x in _port_decls]
    make_indent( port_defs, 1 )
    make_indent( port_decls, 2 )
    return {
      'def' : '\n'.join( port_defs ),
      'decl' : ',\n'.join( port_decls )
    }

  def rtlir_tr_subcomp_port_decl( s, m, c_id, c_rtype, c_array_type, port_id,
      port_rtype, port_dtype, port_array_type ):
    port_def_rtype = rt.Wire(port_dtype["raw_dtype"])

    return {
      'def' : s.rtlir_tr_wire_decl('{c_id}__'+port_id, port_def_rtype,
                port_array_type, port_dtype),
      'decl' : f'.{port_id}( {{c_id}}__{port_id} )'
    }

  def rtlir_tr_subcomp_ifc_port_decls( s, _ifc_port_decls ):
    port_defs, port_decls = [], []

    for ifc_port_decls in _ifc_port_decls:
      port_defs  += [x['def'] for x in ifc_port_decls]
      port_decls += [x['decl'] for x in ifc_port_decls]

    make_indent( port_defs, 1 )
    make_indent( port_decls, 2 )
    return {
      'def' : '\n'.join( port_defs ),
      'decl' : ',\n'.join( port_decls )
    }

  def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, port_id, port_rtype,
      port_array_type ):

    def _flatten_ifc_array( cur_ifc_id, n_dim ):
      nonlocal s, m, c_id, c_rtype, c_array_type
      nonlocal port_id, port_rtype, port_array_type
      ret = []

      if not n_dim:
        all_ifc_properties = port_rtype.get_all_properties_packed()
        for _port_id, _port_rtype in all_ifc_properties:
          if isinstance( _port_rtype, rt.Array ):
            _port_array_rtype = _port_rtype
            _port_rtype = _port_rtype.get_sub_type()
          else:
            _port_array_rtype = None
            _port_rtype = _port_rtype

          ret += s.rtlir_tr_subcomp_ifc_port_decl( m, c_id, c_rtype, c_array_type,
                   f"{cur_ifc_id}__{port_id}", port_rtype, port_array_type,
                   _port_id, _port_rtype, s.rtlir_tr_unpacked_array_type( _port_array_rtype ) )

      else:
        for i in range( n_dim[0] ):
          ret += _flatten_ifc_array( f"{cur_ifc_id}__{i}", n_dim[1:] )

      return ret

    if isinstance( port_rtype, rt.Port ):
      port_dtype = s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      port_def_rtype = rt.Wire(port_dtype["raw_dtype"])

      return [ {
        'def' : s.rtlir_tr_wire_decl(f'{{c_id}}__{ifc_id}__{port_id}', port_def_rtype,
                  port_array_type, port_dtype),
        'decl' : f'.{ifc_id}__{port_id}( {{c_id}}__{ifc_id}__{port_id} )'
      } ]

    else:
      # Support nested interface
      assert isinstance( port_rtype, rt.InterfaceView )
      return _flatten_ifc_array( ifc_id, port_array_type['n_dim'] )

  def rtlir_tr_subcomp_ifc_decls( s, _ifc_decls ):
    # _ifc_decls = sum( _ifc_decls, [] )
    ifc_defs = [x['def'] for x in _ifc_decls]
    ifc_decls = [x['decl'] for x in _ifc_decls]
    return {
      'def' : '\n'.join( ifc_defs ),
      'decl' : ',\n'.join( ifc_decls )
    }

  def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, ports ):
    return ports

  def rtlir_tr_subcomp_decls( s, subcomps ):
    subcomp_decls = sum( subcomps, [] )
    return '\n\n'.join( subcomp_decls )

  def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):

    _c_name = s.rtlir_tr_component_unique_name( c_rtype )

    def gen_subcomp_array_decl( c_id, port_conns, ifc_conns, n_dim, c_n_dim ):
      nonlocal _c_name
      nonlocal m
      tplt = \
"""\
{port_wire_defs}{ifc_inst_defs}

  {c_name} {c_id}
  (
{port_conn_decls}{ifc_conn_decls}
  );\
"""
      if not n_dim:
        # Add the component dimension to the defs/decls

        # Get the object from the hierarchy
        _n_dim = list(int(num_str) for num_str in c_n_dim.split('__') if num_str)
        attr = c_id + ''.join(f'[{dim}]' for dim in _n_dim)
        obj = eval(f'm.{attr}')

        if isinstance(obj, Placeholder):
          c_name = obj.config_placeholder.pickled_top_module
        else:
          c_name = _c_name

        c_id = c_id + c_n_dim
        port_wire_defs = port_conns['def'].format( **locals() )
        ifc_inst_defs = ifc_conns['def'].format( **locals() )
        if port_wire_defs and ifc_inst_defs:
          port_wire_defs += '\n'
        port_conn_decls = port_conns['decl'].format( **locals() )
        ifc_conn_decls = ifc_conns['decl'].format( **locals() )
        if port_conn_decls and ifc_conn_decls:
          port_conn_decls += '\n'
        return [ tplt.format( **locals() ) ]

      else:
        return sum( [gen_subcomp_array_decl( c_id,
            port_conns, ifc_conns, n_dim[1:], c_n_dim+'__'+str(idx) ) \
                for idx in range( n_dim[0] )], [] )

    # If `c_array_type` is not None we need to impelement an array of
    # components, each with their own connections for the ports.
    # This means we will only support component indexing where the index
    # is a constant integer.
    n_dim = c_array_type['n_dim']
    if port_conns['decl'] and ifc_conns['decl']:
      port_conns['decl'] += ','
    return\
      gen_subcomp_array_decl( c_id, port_conns, ifc_conns, n_dim, '' )

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_component_array_index( s, base_signal, index ):
    return f'{base_signal}__{index}'

  def rtlir_tr_subcomp_attr( s, base_signal, attr ):
    return f'{base_signal}__{attr}'
