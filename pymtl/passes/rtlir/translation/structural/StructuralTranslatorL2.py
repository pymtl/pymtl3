#=========================================================================
# StructuralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 24, 2019
"""Provide L2 structural translator."""
from __future__ import absolute_import, division, print_function

from functools import reduce

import pymtl
from pymtl.passes.rtlir.RTLIRDataType import Struct
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import (
    PackedIndex,
    StructAttr,
)

from .StructuralTranslatorL1 import StructuralTranslatorL1


class StructuralTranslatorL2( StructuralTranslatorL1 ):

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, top ):
    top.apply( StructuralRTLIRGenL2Pass() )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, top ):
    # Declarations
    s.structural.decl_type_struct = []
    super( StructuralTranslatorL2, s ).translate_structural( top )

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
    if isinstance( dtype, Struct ):
      ret = s.rtlir_tr_struct_dtype( dtype )
      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_struct, True ):
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

    Add support for the following operations at L2: PackedIndex, StructAttr
    """
    if isinstance( expr, PackedIndex ):
      return s.rtlir_tr_packed_index(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_index())
    elif isinstance( expr, StructAttr ):
      return s.rtlir_tr_struct_attr(
        s.rtlir_signal_expr_translation(expr.get_base(), m), expr.get_attr())
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
