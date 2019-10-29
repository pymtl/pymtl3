#=========================================================================
# SVStructuralTranslatorL4.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.util.utility import make_indent
from pymtl3.passes.translator.structural.StructuralTranslatorL4 import (
    StructuralTranslatorL4,
)

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
    port_defs = [x['def'] for x in _ifc_port_decls]
    port_decls = [x['decl'] for x in _ifc_port_decls]
    make_indent( port_defs, 1 )
    make_indent( port_decls, 2 )
    return {
      'def' : '\n'.join( port_defs ),
      'decl' : ',\n'.join( port_decls )
    }

  def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, port_id, port_rtype,
      port_array_type ):
    assert isinstance( port_rtype, rt.Port ), \
      f"SystemVerilog backend does not support nested interface {port_id} yet!"
    port_dtype = s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
    port_def_rtype = rt.Wire(port_dtype["raw_dtype"])

    return {
      'def' : s.rtlir_tr_wire_decl('{c_id}__{ifc_id}__'+port_id, port_def_rtype,
                port_array_type, port_dtype),
      'decl' : f'.{{ifc_id}}__{port_id}( {{c_id}}__{{ifc_id}}__{port_id} )'
    }

  def rtlir_tr_subcomp_ifc_decls( s, _ifc_decls ):
    _ifc_decls = sum( _ifc_decls, [] )
    ifc_defs = [x['def'] for x in _ifc_decls]
    ifc_decls = [x['decl'] for x in _ifc_decls]
    return {
      'def' : '\n'.join( ifc_defs ),
      'decl' : ',\n'.join( ifc_decls )
    }

  def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, ports ):

    def gen_subcomp_ifc_decl( ifc_id, ifc_rtype, n_dim, c_n_dim, ports ):
      if not n_dim:
        c_id = '{c_id}'
        ifc_id = ifc_id + c_n_dim
        return [ {
          'def' : ports['def'].format( **locals() ),
          'decl' : ports['decl'].format( **locals() )
        } ]
      else:
        return sum( [gen_subcomp_ifc_decl( ifc_id, ifc_rtype, n_dim[1:],
            c_n_dim+'__'+str( idx ), ports ) for idx in range( n_dim[0] )], [] )

    n_dim = ifc_array_type[ 'n_dim' ]
    return \
      gen_subcomp_ifc_decl( ifc_id, ifc_rtype, n_dim, "", ports )

  def rtlir_tr_subcomp_decls( s, subcomps ):
    subcomp_decls = sum( subcomps, [] )
    return '\n\n'.join( subcomp_decls )

  def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):

    _c_name = s.rtlir_tr_component_unique_name( c_rtype )

    def gen_subcomp_array_decl( c_id, port_conns, ifc_conns, n_dim, c_n_dim ):
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
        c_id = c_id + c_n_dim
        c_name = _c_name
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
