#=========================================================================
# VStructuralTranslatorL4.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from textwrap import dedent

from pymtl3.passes.backends.generic.structural.StructuralTranslatorL4 import (
    StructuralTranslatorL4,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRGetter
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.RTLIRPass import RTLIRPass

from ...util.utility import make_indent, pretty_concat
from ...VerilogPlaceholder import VerilogPlaceholder
from .VStructuralTranslatorL3 import VStructuralTranslatorL3


class VStructuralTranslatorL4(
    VStructuralTranslatorL3, StructuralTranslatorL4 ):

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_subcomp_port_decls( s, _port_decls ):
    return _port_decls

  def rtlir_tr_subcomp_port_decl( s, m, c_id, c_rtype, c_array_type, port_id,
      port_rtype, port_dtype, port_array_type ):
    obj = c_rtype.obj
    if obj.has_metadata(s._placeholder_pass.placeholder_config):
      pmap = obj.get_metadata(s._placeholder_pass.placeholder_config).get_port_map()
    else:
      pmap= lambda x: x
    direction = port_rtype.get_direction()
    if direction == 'input':
      direction += ' '
    vname = port_id
    port_full_name = f"{obj}.{port_id}"
    ph_id = vname if pmap(port_full_name) == port_full_name else pmap(port_full_name)
    return {
        'direction' : direction,
        'data_type' : port_dtype['data_type'],
        'packed_type' : port_dtype['packed_type'],
        'id' : port_id,
        'ph_id' : ph_id,
        'unpacked_type' : port_array_type['unpacked_type'],
    }

  def rtlir_tr_subcomp_ifc_port_decls( s, _ifc_port_decls ):
    return sum(_ifc_port_decls, [])

  def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, port_id, port_rtype, port_array_type ):
    if isinstance( port_rtype, rt.Port ):
      obj = c_rtype.obj
      if obj.has_metadata(s._placeholder_pass.placeholder_config):
        pmap = obj.get_metadata(s._placeholder_pass.placeholder_config).get_port_map()
      else:
        pmap = lambda x: x
      vname = f'{ifc_id}__{port_id}'
      pyname = vname.replace('__', '.')
      port_full_name = f"{obj}.{pyname}"
      ph_id = vname if pmap(port_full_name) == port_full_name else pmap(port_full_name)
      port_dtype = s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      direction = port_rtype.get_direction()
      if direction == 'input':
        direction += ' '
      return [{
          'direction' : direction,
          'data_type' : port_dtype['data_type'],
          'packed_type' : port_dtype['packed_type'],
          'id' : vname,
          'ph_id' : ph_id,
          'unpacked_type' : ifc_array_type['unpacked_type']+port_array_type['unpacked_type'],
      }]
    else:
      # Nested interface
      ret = []
      all_properties = port_rtype.get_all_properties_packed()
      for _port_id, _port_rtype in all_properties:
        if isinstance(_port_rtype, rt.Array):
          _port_array_rtype = _port_rtype
          _port_rtype = _port_rtype.get_sub_type()
        else:
          _port_array_rtype = None
          _port_rtype = _port_rtype

        # Combine the array_type of two interfaces into one
        combined_ifc_array_type = {
            'def' : port_array_type['def'],
            'unpacked_type' : ifc_array_type['unpacked_type'] + port_array_type['unpacked_type'],
            'n_dim' : ifc_array_type['n_dim'] + port_array_type['n_dim'],
        }

        ret += s.rtlir_tr_subcomp_ifc_port_decl( m,
                  # Component: nested interface does not change the component
                  c_id, c_rtype, c_array_type,
                  # Interface: nested interface appends its id and array_type
                  f'{ifc_id}__{port_id}', port_rtype, combined_ifc_array_type,
                  # Port: use the id, rtype, and array_type of the port
                  _port_id, _port_rtype, s.rtlir_tr_unpacked_array_type(_port_array_rtype))
      return ret

  def rtlir_tr_subcomp_ifc_decls( s, _ifc_decls ):
    return sum(_ifc_decls, [])

  def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_type, ports ):
    return ports

  def rtlir_tr_subcomp_decls( s, subcomps ):
    subcomp_decls = sum( subcomps, [] )
    return '\n\n'.join( subcomp_decls )

  def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):

    def pretty_comment( string ):
      comments = [
          '  //-------------------------------------------------------------',
         f'  // {string}',
          '  //-------------------------------------------------------------',
      ]
      return '\n'.join(comments)

    def gen_subcomp_array_decl( c_id, port_conns, ifc_conns, n_dim, c_n_dim ):
      nonlocal m, s
      tplt = dedent(
          """\
            {c_name} {c_id}
            (
          {port_conn_decls}
            );""")
      if not n_dim:
        # Get the object from the hierarchy
        _n_dim = list(int(num_str) for num_str in c_n_dim.split('__') if num_str)
        attr = c_id + ''.join(f'[{dim}]' for dim in _n_dim)
        obj = eval(f'm.{attr}')
        # Get the translated component name
        obj_c_rtype = s.tr_top.get_metadata(RTLIRPass.rtlir_getter).get_rtlir(obj)
        _c_name = s.rtlir_tr_component_unique_name(obj_c_rtype)

        # Check to see if explicit_module_name is present
        from pymtl3.passes.backends.verilog.translation.VerilogTranslationPass import (
            VerilogTranslationPass,
        )
        if obj.has_metadata( VerilogTranslationPass.explicit_module_name ):
          subcomp_explicit_name = obj.get_metadata( VerilogTranslationPass.explicit_module_name )
        else:
          subcomp_explicit_name = ''

        if isinstance(obj, VerilogPlaceholder):
          c_name = obj.get_metadata( s._placeholder_pass.placeholder_config ).pickled_top_module
        elif subcomp_explicit_name:
          # If someone sets explicit_module_name, we need to honor that config
          c_name = subcomp_explicit_name
        else:
          c_name = _c_name

        orig_c_id = c_id
        c_id = c_id + c_n_dim

        # Generate correct connections
        port_conn_decls = []
        unpacked_str = ''.join([f'[{i}]' for i in _n_dim])

        no_clk   = s.structural.component_no_synthesis_no_clk[obj]
        no_reset = s.structural.component_no_synthesis_no_reset[obj]

        for i, dscp in enumerate(port_conns + ifc_conns):
          comma = ',\n' if i != len(port_conns+ifc_conns)-1 else ''
          port_name = dscp['id']
          ph_port_name = dscp['ph_id']
          port_wire = f"{orig_c_id}__{dscp['id']}{unpacked_str}"
          if (port_name == 'clk' and no_clk) or (port_name == 'reset' and no_reset):
            comma = ',\n' if i != len(port_conns+ifc_conns)-1 else '\n'
            newline = '\n' if i != len(port_conns+ifc_conns)-1 else ''
            port_conn_decls.append("`ifndef SYNTHESIS\n")
            port_conn_decls.append(f".{ph_port_name}( {port_wire} ){comma}")
            port_conn_decls.append(f"`endif{newline}")
          else:
            port_conn_decls.append(f".{ph_port_name}( {port_wire} ){comma}")

        make_indent( port_conn_decls, 2 )
        port_conn_decls = ''.join(port_conn_decls)
        return [ tplt.format( **locals() ) ]

      else:
        return sum( [gen_subcomp_array_decl( c_id,
            port_conns, ifc_conns, n_dim[1:], c_n_dim+'__'+str(idx) ) \
                for idx in range( n_dim[0] )], [] )

    # If `c_array_type` is not None we need to impelement an array of
    # components, each with their own connections for the ports.

    # Generate wire declarations for all ports
    defs = []

    for dscp in port_conns + ifc_conns:
      defs.append(pretty_concat(dscp['data_type'], dscp['packed_type'],
        f"{c_id}__{dscp['id']}", f"{c_array_type['unpacked_type']}{dscp['unpacked_type']}", ';'))

    make_indent( defs, 1 )
    defs = ['\n'.join(defs)]

    n_dim = c_array_type['n_dim']
    subcomps = gen_subcomp_array_decl( c_id, port_conns, ifc_conns, n_dim, '' )

    return [pretty_comment(f"Component {c_id}{c_array_type['unpacked_type']}")] + \
           defs + subcomps + \
           [pretty_comment(f"End of component {c_id}{c_array_type['unpacked_type']}")]

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_component_array_index( s, base_signal, index, status ):
    s._rtlir_tr_unpacked_q.append( index )
    return base_signal

  def rtlir_tr_subcomp_attr( s, base_signal, attr, status ):
    return s._rtlir_tr_process_unpacked(
              f'{base_signal}__{attr}',
              f'{base_signal}__{attr}{{}}',
              status, ('status') )
