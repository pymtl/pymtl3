#=========================================================================
# StructuralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 24, 2019
"""Provide L2 structural translator."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)

from .StructuralTranslatorL1 import StructuralTranslatorL1


class StructuralTranslatorL2( StructuralTranslatorL1 ):

  def __init__( s, top ):
    super().__init__( top )

  def clear( s, tr_top ):
    super().clear( tr_top )
    # Declarations
    s.structural.decl_type_struct = {}

  #-----------------------------------------------------------------------
  # _get_structural_rtlir_gen_pass
  #-----------------------------------------------------------------------

  # Override
  def _get_structural_rtlir_gen_pass( s ):
    return StructuralRTLIRGenL2Pass

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, tr_top ):
    super().translate_structural( tr_top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  # Override
  def _translate_structural( s, m ):
    super()._translate_structural( m )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):
    super().translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------

  # Override
  def rtlir_data_type_translation( s, m, dtype ):
    def recurse_struct_dtype_translation( dtype ):
      for key, value in dtype.get_all_properties().items():
        if isinstance( value, rdt.PackedArray ):
          value = value.get_sub_dtype()
        if not isinstance(value, rdt.Struct):
          s.rtlir_data_type_translation( m, value )
        else:
          s.rtlir_data_type_translation( m, value )

    if isinstance( dtype, rdt.Struct ):
      ret = s.rtlir_tr_struct_dtype( dtype )
      if dtype not in s.structural.decl_type_struct:
        recurse_struct_dtype_translation( dtype )
        s.structural.decl_type_struct[ dtype ] = ret
      return ret
    else:
      return super().rtlir_data_type_translation( m, dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  # Override
  def rtlir_signal_expr_translation( s, expr, m, status = 'intermediate' ):
    """Translate a signal expression in RTLIR into its backend representation.

    Add support for the following operations at L2: sexp.PackedIndex, sexp.StructAttr
    """
    if isinstance( expr, sexp.PackedIndex ):
      return s.rtlir_tr_packed_index(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_index(), status)
    elif isinstance( expr, sexp.StructAttr ):
      return s.rtlir_tr_struct_attr(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_attr(), status)
    elif isinstance( expr, sexp.ConstInstance ):
      rtype = expr.get_rtype()
      value = expr.get_value()
      dtype = rtype.get_dtype()
      if isinstance( dtype, rdt.Struct ):
        return s.rtlir_tr_struct_instance(dtype, value)
      else:
        return super(). \
            rtlir_signal_expr_translation( expr, m, status )
    else:
      return super(). \
          rtlir_signal_expr_translation( expr, m, status )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types
  def rtlir_tr_struct_dtype( s, Type ):
    raise NotImplementedError()

  # Signal operations
  def rtlir_tr_packed_index( s, base_signal, index, status ):
    raise NotImplementedError()

  def rtlir_tr_struct_attr( s, base_signal, attr, status ):
    raise NotImplementedError()

  def rtlir_tr_struct_instance( s, dtype, struct ):
    raise NotImplementedError()
