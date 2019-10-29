#=========================================================================
# SVStructuralTranslatorL3.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.util.utility import make_indent
from pymtl3.passes.translator.structural.StructuralTranslatorL3 import (
    StructuralTranslatorL3,
)

from .SVStructuralTranslatorL2 import SVStructuralTranslatorL2


class SVStructuralTranslatorL3(
    SVStructuralTranslatorL2, StructuralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_interface_port_decls( s, port_decls ):
    return sum( port_decls, [] )

  def rtlir_tr_interface_port_decl( s, m, port_id, port_rtype, port_array_type ):
    def _gen_ifc( id_, ifc, n_dim ):
      if not n_dim:
        ret = []
        all_properties = ifc.get_all_properties_packed()
        for name, _rtype in all_properties:
          if isinstance( _rtype, rt.Array ):
            array_type = _rtype
            rtype = _rtype.get_sub_type()
          else:
            array_type = None
            rtype = _rtype
          ret += s.rtlir_tr_interface_port_decl(
            m, id_+"__"+name, rtype, s.rtlir_tr_unpacked_array_type( array_type ) )
        return ret
      else:
        ret = []
        for i in range( n_dim[0] ):
          ret += _gen_ifc( id_+"__"+str(i), ifc, n_dim[1:] )
        return ret
    # Port id is appended after the template of interface id:
    #   > `{id_}__msg` where `msg` is an attribute of the interface.
    if isinstance( port_rtype, rt.Port ):
      port_dtype = s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      decl_tmplt = port_rtype.get_direction() + ' ' + \
                   port_dtype['decl'] + '__' + port_id + port_array_type['decl']
      return [ decl_tmplt ]
    else:
      n_dim = port_array_type["n_dim"]
      return _gen_ifc( port_id, port_rtype, n_dim )

  def rtlir_tr_interface_decls( s, ifc_decls ):
    all_decls = sum( ifc_decls, [] )
    make_indent( all_decls, 1 )
    return ',\n'.join( all_decls )

  def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type, port_decls ):
    def gen_interface_array_decl( ifc_id, ifc_rtype, n_dim, c_n_dim, port_decls ):
      # Fill in the interface id to complete the signal name:
      #   > `in_ifc__0__msg` where `__msg` is filled when calling
      # rtlir_tr_interface_port_decl and `id_` = `in_ifc__0`.
      ret = []
      if not n_dim:
        id_ = ifc_id + c_n_dim
        return [pdecl.format( id_ = id_ ) for pdecl in port_decls]
      else:
        return sum( [ gen_interface_array_decl(
          ifc_id, ifc_rtype, n_dim[1:], c_n_dim+"__"+str(idx), port_decls,
        ) for idx in range( n_dim[0] ) ], [] )
    n_dim = array_type['n_dim']
    return gen_interface_array_decl( ifc_id, ifc_rtype, n_dim, '', port_decls )

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_interface_array_index( s, base_signal, index ):
    return f'{base_signal}__{index}'

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    return f'{base_signal}__{attr}'
