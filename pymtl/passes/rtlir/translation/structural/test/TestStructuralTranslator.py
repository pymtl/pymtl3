#=========================================================================
# TestStructuralTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide a structural translator that fits testing purposes."""

from __future__ import absolute_import, division, print_function


def mk_TestStructuralTranslator( _StructuralTranslator ):
  def make_indent( src, nindent ):
    """Add nindent indention to every line in src."""
    indent = '  '
    for idx, s in enumerate( src ):
      src[ idx ] = nindent * indent + s

  def get_string( obj ):
    """Return the string that identifies `obj`"""
    if isinstance(obj, type): return obj.__name__
    return str( obj )

  class TestStructuralTranslator( _StructuralTranslator ):
    def rtlir_tr_vector_dtype( s, Type ):
      return str( Type )

    def rtlir_tr_unpacked_array_type( s, Type ):
      return "" if Type is None else repr( Type )

    def rtlir_tr_port_decls( s, port_decls ):
      decls = ''
      for decl in port_decls:
        if decl:
          make_indent( decl, 1 )
          decls += '\n' + '\n'.join( decl )
      return 'port_decls:{}\n'.format( decls )

    def rtlir_tr_port_decl( s, id_, Type, array_type, dtype ):
      if id_ not in ["clk", "reset"]:
        array_type = repr(Type) if not array_type else array_type
        return ['port_decl: {id_} {array_type}'.format( **locals() )]
      else:
        return ""

    def rtlir_tr_wire_decls( s, wire_decls ):
      decls = ''
      for decl in wire_decls:
        make_indent( decl, 1 )
        decls += '\n' + '\n'.join( decl )
      return 'wire_decls:{}\n'.format( decls )

    def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
      array_type = repr(Type) if not array_type else array_type
      return ['wire_decl: {id_} {array_type}'.format( **locals() )]

    def rtlir_tr_const_decls( s, const_decls ):
      decls = ''
      for decl in const_decls:
        make_indent( decl, 1 )
        decls += '\n' + '\n'.join( decl )
      return 'const_decls:{}\n'.format( decls )

    def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
      array_type = repr(Type) if not array_type else array_type
      return ['const_decl: {id_} {array_type}'.format( **locals() )]

    def rtlir_tr_connections( s, connections ):
      conns = ''
      for conn in connections:
        make_indent( conn, 1 )
        conns += '\n' + '\n'.join( conn )
      return 'connections:{}\n'.format( conns )

    def rtlir_tr_connection( s, wr, rd ):
      return ['connection: {wr} -> {rd}'.format( **locals() )]

    def rtlir_tr_bit_selection( s, base_signal, index ):
      return 'BitSel {base_signal} {index}'.format( **locals() )

    def rtlir_tr_part_selection( s, base_signal, start, stop ):
      return 'PartSel {base_signal} {start} {stop}'.format( **locals() )

    def rtlir_tr_port_array_index( s, base_signal, index ):
      return 'PortArrayIdx {base_signal} {index}'.format( **locals() )

    def rtlir_tr_wire_array_index( s, base_signal, index ):
      return 'WireArrayIdx {base_signal} {index}'.format( **locals() )

    def rtlir_tr_const_array_index( s, base_signal, index ):
      return 'ConstArrayIdx {base_signal} {index}'.format( **locals() )

    def rtlir_tr_current_comp_attr( s, base_signal, attr ):
      return 'CurCompAttr {attr}'.format( **locals() )

    def rtlir_tr_current_comp( s, comp_id, comp_rtype ):
      return ''

    def rtlir_tr_var_id( s, var_id ):
      return var_id

    def rtlir_tr_literal_number( s, nbits, value ):
      return 'Bits{nbits}({value})'.format( **locals() )

    def rtlir_tr_component_unique_name( s, c_rtype ):
      comp_name = c_rtype.get_name()
      comp_params = c_rtype.get_params()
      assert comp_name
      for arg_name, arg_value in comp_params:
        assert arg_name != ''
        comp_name += '__' + arg_name + '_' + get_string(arg_value)
      return comp_name

  return TestStructuralTranslator
