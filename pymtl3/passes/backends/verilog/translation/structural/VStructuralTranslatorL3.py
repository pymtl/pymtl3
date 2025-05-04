#=========================================================================
# VStructuralTranslatorL3.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3.passes.backends.generic.structural.StructuralTranslatorL3 import (
    StructuralTranslatorL3,
)
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt

from pymtl3.passes.backends.verilog.VerilogPlaceholder import VerilogPlaceholder
from pymtl3.passes.backends.verilog.VerilogPlaceholderPass import VerilogPlaceholderPass

from ...util.utility import make_indent, pretty_concat
from .VStructuralTranslatorL2 import VStructuralTranslatorL2


class VStructuralTranslatorL3(
    VStructuralTranslatorL2, StructuralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def rtlir_tr_interface_port_decls( s, m, port_decls ):
    return sum( port_decls, [] )

  def rtlir_tr_interface_port_decl( s, m, port_id, port_rtype, port_array_type ):
    if isinstance( port_rtype, rt.Port ):
      port_dtype = s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      if port_array_type is None:
        # Non-array interface port
        return [ {
          'direction' : port_rtype.get_direction(),
          'data_type' : port_dtype['data_type'],
          'packed_type' : port_dtype['packed_type'],
          'unpacked_type' : port_dtype['unpacked_type'],
          'id' : port_id,
        } ]
      else:
        # Array interface port
        return [ {
          'direction' : port_rtype.get_direction(),
          'data_type' : port_dtype['data_type'],
          'packed_type' : port_dtype['packed_type'],
          'unpacked_type' : pretty_concat(port_array_type['unpacked_type'], port_dtype['unpacked_type']),
          'id' : port_id,
        } ]
    else:
      # Nested interface
      sep = s._get_separator_symbol( m )
      dscps = []
      all_properties = port_rtype.get_all_properties_packed()
      for name, _rtype in all_properties:
        if isinstance( _rtype, rt.Array ):
          array_type = _rtype
          rtype = _rtype.get_sub_type()
        else:
          array_type = None
          rtype = _rtype
        # Name-mangle the nested interface
        dscp = s.rtlir_tr_interface_port_decl(m, f'{port_id}{sep}{name}', rtype, array_type)
        # Add unpacked_type of the current interface to the unpacked_type of the port
        for tr in dscp:
          tr['unpacked_type'] = port_array_type['unpacked_type'] + tr['unpacked_type']
        dscps += dscp
      return dscps

  def rtlir_tr_interface_decls( s, m, ifc_decls ):
    all_decls = sum( ifc_decls, [] )
    make_indent( all_decls, 1 )
    return ',\n'.join( all_decls )

  def rtlir_tr_interface_decl( s, m, ifc_id, ifc_rtype, array_type, port_decls ):
    decls = []
    sep = s._get_separator_symbol( m )
    for tr in port_decls:
      direc = tr['direction']
      data_type = tr['data_type']
      packed_type = tr['packed_type']
      id = f"{ifc_id}{sep}{tr['id']}"
      unpacked_type = array_type['unpacked_type'] + tr['unpacked_type']
      decls.append(pretty_concat(direc, data_type, packed_type, id, unpacked_type))
    return decls

  #-----------------------------------------------------------------------
  # Signal operations
  #-----------------------------------------------------------------------

  def rtlir_tr_interface_array_index( s, m, base_signal, index, status ):
    s._rtlir_tr_unpacked_q.append( index )
    return base_signal

  def rtlir_tr_interface_attr( s, m, base_signal, attr, status ):
    sep = s._get_separator_symbol( m )
    return s._rtlir_tr_process_unpacked(
              f'{base_signal}{sep}{attr}',
              f'{base_signal}{sep}{attr}{{}}',
              status, ('status') )

  #-----------------------------------------------------------------------
  # Helpers
  #-----------------------------------------------------------------------

  @staticmethod
  def _get_separator_symbol( m ):
    if isinstance( m, VerilogPlaceholder ):
      # If the given component is a placeholder, we use whatever separator
      # symbol the user provides through placeholder configuration.
      ph_cfg = m.get_metadata( VerilogPlaceholderPass.placeholder_config )
      return ph_cfg.separator
    # Otherwise we default to a double underscore.
    return "__"
