#=========================================================================
# StructuralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 4, 2019
"""Provide L4 structural translator."""

from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL4Pass import (
    StructuralRTLIRGenL4Pass,
)

from .StructuralTranslatorL3 import StructuralTranslatorL3


class StructuralTranslatorL4( StructuralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # _get_structural_rtlir_gen_pass
  #-----------------------------------------------------------------------

  # Override
  def _get_structural_rtlir_gen_pass( s ):
    return StructuralRTLIRGenL4Pass

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, tr_top ):
    s.structural.decl_subcomps = {}
    super().translate_structural( tr_top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  # Override
  def _translate_structural( s, m ):
    super()._translate_structural( m )
    for child in m.get_child_components(repr):
      s._translate_structural( child )

  # Override
  def translate_decls( s, m ):
    super().translate_decls( m )
    m_rtype = m.get_metadata( StructuralRTLIRGenL4Pass.rtlir_type )

    # Translate subcomponent declarations
    subcomp_decls = []
    for c_id, _c_rtype in m_rtype.get_subcomps_packed():
      if isinstance( _c_rtype, rt.Array ):
        c_array_rtype = _c_rtype
        c_rtype = _c_rtype.get_sub_type()
      else:
        c_array_rtype = None
        c_rtype = _c_rtype

      # Translate ports of the subcomponent
      port_conns, ifc_conns = [], []
      for port_id, _port_rtype in c_rtype.get_ports_packed():
        if isinstance( _port_rtype, rt.Array ):
          port_array_rtype = _port_rtype
          port_rtype = _port_rtype.get_sub_type()
        else:
          port_array_rtype = None
          port_rtype = _port_rtype

        port_conns.append( s.rtlir_tr_subcomp_port_decl(
          m,
          c_id, c_rtype, s.rtlir_tr_unpacked_array_type( c_array_rtype ),
          port_id, port_rtype,
          s.rtlir_data_type_translation( m, port_rtype.get_dtype() ),
          s.rtlir_tr_unpacked_array_type( port_array_rtype )
        ) )

      # Translate interfaces of the subcomponent
      for ifc_port_id, _ifc_port_rtype in c_rtype.get_ifc_views_packed():
        if isinstance( _ifc_port_rtype, rt.Array ):
          ifc_port_array_rtype = _ifc_port_rtype
          ifc_port_rtype = _ifc_port_rtype.get_sub_type()
        else:
          ifc_port_array_rtype = None
          ifc_port_rtype = _ifc_port_rtype

        ports = []
        all_ifc_ports = ifc_port_rtype.get_all_properties_packed()
        for port_id, p_rtype in all_ifc_ports:
          if isinstance( p_rtype, rt.Array ):
            port_array_rtype = p_rtype
            port_rtype = p_rtype.get_sub_type()
          else:
            port_array_rtype = None
            port_rtype = p_rtype

          # Translate a single port of the current interface
          ports.append( s.rtlir_tr_subcomp_ifc_port_decl(
            m,
            '{c_id}', c_rtype, s.rtlir_tr_unpacked_array_type( c_array_rtype ),
            ifc_port_id, ifc_port_rtype,
            s.rtlir_tr_unpacked_array_type( ifc_port_array_rtype ),
            port_id, port_rtype,
            s.rtlir_tr_unpacked_array_type( port_array_rtype )
          ) )

        # Assemble all ports of the current interface into a complete interface
        ifc_conns.append( s.rtlir_tr_subcomp_ifc_decl(
          m,
          '{c_id}', c_rtype, s.rtlir_tr_unpacked_array_type( c_array_rtype ),
          ifc_port_id, ifc_port_rtype,
          s.rtlir_tr_unpacked_array_type( ifc_port_array_rtype ),
          s.rtlir_tr_subcomp_ifc_port_decls( ports )
        ) )

      # Generate a list of ports and interfaces
      subcomp_decls.append( s.rtlir_tr_subcomp_decl(
        m,
        c_id, c_rtype, s.rtlir_tr_unpacked_array_type( c_array_rtype ),
        s.rtlir_tr_subcomp_port_decls( port_conns ),
        s.rtlir_tr_subcomp_ifc_decls( ifc_conns )
      ) )
    s.structural.decl_subcomps[m] = s.rtlir_tr_subcomp_decls( subcomp_decls )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  def rtlir_signal_expr_translation( s, expr, m, status = 'intermediate' ):
    """Translate a signal expression in RTLIR into its backend representation.

    Add support for the following operations at L4: sexp.SubCompAttr
    """
    if isinstance( expr, sexp.SubCompAttr ):
      return s.rtlir_tr_subcomp_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr(), status )

    elif isinstance( expr, sexp.ComponentIndex ):
      return s.rtlir_tr_component_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index(), status )

    else:
      return super(). \
              rtlir_signal_expr_translation( expr, m, status )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend
  #-----------------------------------------------------------------------

  # Declarations
  def rtlir_tr_subcomp_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_port_decl( s, m, c_id, c_rtype, c_array_type, port_id, port_rtype,
      port_dtype, port_array_type ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_decls( s, ifc_decls ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_decl( s, m, c_id, c_rtype, c_array_type, ifc_port_id,
      ifc_port_rtype, ifc_port_array_type, ports ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_port_decls( s, ifc_port_decls ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_port_decl( s, m, c_id, c_rtype, c_array_type,
      ifc_id, ifc_rtype, ifc_array_rtype, port_id, port_rtype,
      port_array_type ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_decls( s, subcomps ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_decl( s, m, c_id, c_rtype, c_array_type, port_conns, ifc_conns ):
    raise NotImplementedError()

  # Signal operations
  def rtlir_tr_component_array_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_attr( s, base_signal, attr, status ):
    raise NotImplementedError()
