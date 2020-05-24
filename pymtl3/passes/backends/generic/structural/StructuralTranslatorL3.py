#=========================================================================
# StructuralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 4, 2019
"""Provide L3 structural translator."""

from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL3Pass import (
    StructuralRTLIRGenL3Pass,
)

from .StructuralTranslatorL2 import StructuralTranslatorL2


class StructuralTranslatorL3( StructuralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # _get_structural_rtlir_gen_pass
  #-----------------------------------------------------------------------

  # Override
  def _get_structural_rtlir_gen_pass( s ):
    return StructuralRTLIRGenL3Pass

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, tr_top ):
    s.structural.decl_ifcs = {}
    super().translate_structural( tr_top )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):
    m_rtype = m.get_metadata( StructuralRTLIRGenL3Pass.rtlir_type )

    # Interfaces
    ifc_decls = []
    for ifc_id, rtype in m_rtype.get_ifc_views_packed():
      if isinstance( rtype, rt.Array ):
        array_rtype = rtype
        ifc_rtype = rtype.get_sub_type()
      else:
        array_rtype = None
        ifc_rtype = rtype

      # Translate all ports and interfaces inside the interface
      ports = []
      all_properties = ifc_rtype.get_all_properties_packed()
      for p_id, _p_rtype in all_properties:
        if isinstance( _p_rtype, rt.Array ):
          p_array_rtype = _p_rtype
          p_rtype = _p_rtype.get_sub_type()
        else:
          p_array_rtype = None
          p_rtype = _p_rtype

        ports.append( s.rtlir_tr_interface_port_decl(
          m,
          s.rtlir_tr_var_id( p_id ),
          p_rtype,
          s.rtlir_tr_unpacked_array_type( p_array_rtype ),
        ) )
      ifc_decls.append(
        s.rtlir_tr_interface_decl(
          ifc_id,
          ifc_rtype,
          s.rtlir_tr_unpacked_array_type( array_rtype ),
          s.rtlir_tr_interface_port_decls( ports )
      ) )
    s.structural.decl_ifcs[m] = s.rtlir_tr_interface_decls( ifc_decls )

    super().translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  # Override
  def rtlir_signal_expr_translation( s, expr, m, status = 'intermediate' ):
    """Translate a signal expression in RTLIR into its backend representation.

    Add support for the following operations at L3: sexp.InterfaceAttr
    """
    if isinstance( expr, sexp.InterfaceAttr ):
      return s.rtlir_tr_interface_attr(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_attr(), status)

    elif isinstance( expr, sexp.InterfaceViewIndex ):
      return s.rtlir_tr_interface_array_index(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_index(), status)

    else:
      return super().rtlir_signal_expr_translation(expr, m, status)

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Declarations
  def rtlir_tr_interface_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_port_decl( s, m, port_id, port_rtype, port_array_type ):
    raise NotImplementedError()

  def rtlir_tr_interface_decls( s, ifc_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type, port_decls ):
    raise NotImplementedError()

  # Signal operations
  def rtlir_tr_interface_array_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_interface_attr( s, base_signal, attr, status ):
    raise NotImplementedError()
