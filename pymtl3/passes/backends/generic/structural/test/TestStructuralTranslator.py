#=========================================================================
# TestStructuralTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide a structural translator that fits testing purposes."""

from .. import StructuralTranslator


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
    """Testing translator that implements structural callback methods."""

    def rtlir_tr_vector_dtype( s, dtype ):
      return str( dtype )

    def rtlir_tr_struct_dtype( s, dtype ):
      return dtype.get_name()

    def rtlir_tr_unpacked_array_type( s, Type ):
      return "" if Type is None else repr( Type )

    def rtlir_tr_port_decls( s, port_decls ):
      decls = ''
      for decl in port_decls:
        if decl:
          make_indent( decl, 1 )
          decls += '\n' + '\n'.join( decl )
      return f'port_decls:{decls}\n'

    def rtlir_tr_port_decl( s, id_, Type, array_type, dtype ):
      if id_ not in ["clk", "reset"]:
        array_type = repr(Type) if not array_type else array_type
        return [f'port_decl: {id_} {array_type}']
      else:
        return ""

    def rtlir_tr_wire_decls( s, wire_decls ):
      decls = ''
      for decl in wire_decls:
        make_indent( decl, 1 )
        decls += '\n' + '\n'.join( decl )
      return f'wire_decls:{decls}\n'

    def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
      array_type = repr(Type) if not array_type else array_type
      return [f'wire_decl: {id_} {array_type}']

    def rtlir_tr_const_decls( s, const_decls ):
      decls = ''
      for decl in const_decls:
        if decl:
          make_indent( decl, 1 )
          decls += '\n' + '\n'.join( decl )
      return f'const_decls:{decls}\n'

    def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
      array_type = repr(Type) if not array_type else array_type
      return [f'const_decl: {id_} {array_type}']

    def rtlir_tr_interface_port_decls( s, port_decls ):
      decls = [['interface_ports:']]
      for decl in port_decls:
        make_indent( decl, 1 )
        decls.append( [ decl[0] ] )
      return decls

    def rtlir_tr_interface_port_decl( s, m, id_, rtype, array_type ):
      rtype = repr(rtype) if not array_type else array_type
      return [f'interface_port: {id_} {rtype}']

    def rtlir_tr_interface_decls( s, ifc_decls ):
      decls = ''
      for decl in ifc_decls:
        if decl:
          make_indent( decl, 1 )
          decls += '\n' + '\n'.join( decl )
      return f'interface_decls:{decls}\n'

    def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type, port_decls ):
      ifc_rtype = str(ifc_rtype) if not array_type else array_type
      ret = [f'interface_decl: {ifc_id} {ifc_rtype}']
      for decl in port_decls:
        make_indent( decl, 1 )
        ret.append( decl[0] )
      return ret

    def rtlir_tr_subcomp_port_decls( s, port_decls ):
      decls = [['component_ports:']]
      for decl in port_decls:
        if decl:
          make_indent( decl, 1 )
          decls.append( [ decl[0] ] )
      return decls

    def rtlir_tr_subcomp_port_decl( s, m, c_id, c_rtype, c_array_type, port_id,
        port_rtype, port_dtype, array_type ):
      if port_id not in ["clk", "reset"]:
        port_rtype = repr(port_rtype) if not array_type else array_type
        return [f'component_port: {port_id} {port_rtype}']
      else:
        return ""

    def rtlir_tr_subcomp_ifc_port_decls( s, ifc_port_decls ):
      decls = [['component_ifc_ports:']]
      for decl in ifc_port_decls:
        if decl:
          make_indent( decl, 1 )
          decls.append( [ decl[0] ] )
      return decls

    def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
        ifc_id, ifc_rtype, ifc_array_type, port_id, port_rtype,
        port_array_type ):
      port_rtype = repr(port_rtype) if not port_array_type else port_array_type
      return [f'component_ifc_port: {port_id} {port_rtype}']

    def rtlir_tr_subcomp_ifc_decls( s, ifc_decls ):
      decls = [['component_ifcs:']]
      for ifc_decl in ifc_decls:
        for decl in ifc_decl:
          if decl:
            make_indent( decl, 1 )
            decls.append( [ decl[0] ] )
      return decls

    def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type, ifc_id,
        ifc_rtype, ifc_array_type, ports ):
      ifc_rtype = repr(ifc_rtype) if not ifc_array_type else ifc_array_type
      decls = [[f'component_ifc: {ifc_id} {ifc_rtype}']]
      for decl in ports:
        if decl:
          make_indent( decl, 1 )
          decls.append( [ decl[0] ] )
      return decls

    def rtlir_tr_subcomp_decls( s, subcomps ):
      decls = ''
      for decl in subcomps:
        make_indent( decl, 1 )
        decls += '\n' + '\n'.join( decl )
      return f'component_decls:{decls}\n'

    def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):
      c_rtype = str(c_rtype) if not c_array_type else c_array_type
      ret = [f'component_decl: {c_id} {c_rtype}']
      for port in port_conns:
        make_indent( port, 1 )
        ret.append( port[0] )
      for ifc in ifc_conns:
        make_indent( ifc, 1 )
        ret.append( ifc[0] )
      return ret

    def rtlir_tr_connections( s, connections ):
      conns = ''
      for conn in connections:
        if conn:
          make_indent( conn, 1 )
          conns += '\n' + '\n'.join( conn )
      return f'connections:{conns}\n'

    def rtlir_tr_connection( s, wr, rd ):
      if "clk" not in wr and "reset" not in wr:
        return [f'connection: {wr} -> {rd}']

    def rtlir_tr_bit_selection( s, base_signal, index, status ):
      return f'BitSel {base_signal} {index}'

    def rtlir_tr_part_selection( s, base_signal, start, stop, status ):
      return f'PartSel {base_signal} {start} {stop}'

    def rtlir_tr_port_array_index( s, base_signal, index, status ):
      return f'PortArrayIdx {base_signal} {index}'

    def rtlir_tr_wire_array_index( s, base_signal, index, status ):
      return f'WireArrayIdx {base_signal} {index}'

    def rtlir_tr_const_array_index( s, base_signal, index, status ):
      return f'ConstArrayIdx {base_signal} {index}'

    def rtlir_tr_packed_index( s, base_signal, index, status ):
      return f'PackedIndex {base_signal} {index}'

    def rtlir_tr_interface_array_index( s, base_signal, index, status ):
      return f'IfcArrayIdx {base_signal} {index}'

    def rtlir_tr_component_array_index( s, base_signal, index, status ):
      return f'CompArrayIdx {base_signal} {index}'

    def rtlir_tr_struct_attr( s, base_signal, attr, status ):
      return f'StructAttr {base_signal} {attr}'

    def rtlir_tr_interface_attr( s, base_signal, attr, status ):
      return f'IfcAttr {base_signal} {attr}'

    def rtlir_tr_subcomp_attr( s, base_signal, attr, status ):
      return f'SubCompAttr {base_signal} {attr}'

    def rtlir_tr_current_comp_attr( s, base_signal, attr, status ):
      return f'CurCompAttr {attr}'

    def rtlir_tr_current_comp( s, comp_id, comp_rtype, status ):
      return ''

    def rtlir_tr_var_id( s, var_id ):
      return var_id

    def rtlir_tr_literal_number( s, nbits, value ):
      return f'Bits{nbits}({int(value)})'

    def rtlir_tr_component_unique_name( s, c_rtype ):
      comp_name = c_rtype.get_name()
      comp_params = c_rtype.get_params()
      assert comp_name
      for arg_name, arg_value in comp_params:
        assert arg_name != ''
        comp_name += '__' + arg_name + '_' + get_string(arg_value)
      return comp_name

  return TestStructuralTranslator

TestStructuralTranslator = mk_TestStructuralTranslator( StructuralTranslator )
