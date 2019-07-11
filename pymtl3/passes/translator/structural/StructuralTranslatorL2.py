#=========================================================================
# StructuralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 24, 2019
"""Provide L2 structural translator."""
from __future__ import absolute_import, division, print_function

from functools import reduce

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)

from .StructuralTranslatorL1 import StructuralTranslatorL1


class StructuralTranslatorL2( StructuralTranslatorL1 ):

  def __init__( s, top ):
    super( StructuralTranslatorL2, s ).__init__( top )

  def clear( s, tr_top ):
    super( StructuralTranslatorL2, s ).clear( tr_top )
    # Declarations
    s.structural.decl_type_struct = []

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, tr_top ):
    # c_ss: self-self connections
    # c_sc: self-child connections
    # c_cc: child-child connections
    tr_top.apply( StructuralRTLIRGenL2Pass( s.c_ss, s.c_sc, s.c_cc ) )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, tr_top ):
    super( StructuralTranslatorL2, s ).translate_structural( tr_top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  # Override
  def _translate_structural( s, m ):
    super( StructuralTranslatorL2, s )._translate_structural( m )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):
    super( StructuralTranslatorL2, s ).translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------

  # Override
  def rtlir_data_type_translation( s, m, dtype ):
    def recurse_struct_dtype_translation( dtype ):
      for key, value in dtype.get_all_properties():
        if isinstance( value, rdt.PackedArray ):
          value = value.get_sub_dtype()
        if not isinstance(value, rdt.Struct):
          s.rtlir_data_type_translation( m, value )
        else:
          s.rtlir_data_type_translation( m, value )

    if isinstance( dtype, rdt.Struct ):
      ret = s.rtlir_tr_struct_dtype( dtype )
      ns_struct = s.structural.decl_type_struct
      if reduce(lambda r, x: r and dtype != x[0], ns_struct, True):
        recurse_struct_dtype_translation( dtype )
        s.structural.decl_type_struct.append( ( dtype, ret ) )
      return ret
    else:
      return super( StructuralTranslatorL2, s ). \
          rtlir_data_type_translation( m, dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------

  # Override
  def rtlir_signal_expr_translation( s, expr, m ):
    """Translate a signal expression in RTLIR into its backend representation.

    Add support for the following operations at L2: sexp.PackedIndex, sexp.StructAttr
    """
    if isinstance( expr, sexp.PackedIndex ):
      return s.rtlir_tr_packed_index(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_index())
    elif isinstance( expr, sexp.StructAttr ):
      return s.rtlir_tr_struct_attr(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_attr())
    elif isinstance( expr, sexp.ConstInstance ):
      rtype = expr.get_rtype()
      value = expr.get_value()
      dtype = rtype.get_dtype()
      if isinstance( dtype, rdt.Struct ):
        return s.rtlir_tr_struct_instance(dtype, value)
      else:
        return super( StructuralTranslatorL2, s ). \
            rtlir_signal_expr_translation( expr, m )
    else:
      return super( StructuralTranslatorL2, s ). \
          rtlir_signal_expr_translation( expr, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types
  def rtlir_tr_struct_dtype( s, Type ):
    raise NotImplementedError()

  # Signal operations
  def rtlir_tr_packed_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_struct_attr( s, base_signal, attr ):
    raise NotImplementedError()

  def rtlir_tr_struct_instance( s, dtype, struct ):
    raise NotImplementedError()
