#=========================================================================
# StructuralRTLIRGenL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 3, 2019
"""Provide L4 structural RTLIR generation pass."""

from pymtl3.passes.BasePass import PassMetadata

from .StructuralRTLIRGenL3Pass import StructuralRTLIRGenL3Pass
from .StructuralRTLIRSignalExpr import gen_signal_expr


class StructuralRTLIRGenL4Pass( StructuralRTLIRGenL3Pass ):
  # Override
  def __call__( s, tr_top ):
    s.gen_metadata( tr_top )
    super().__call__( tr_top )

  def gen_metadata( s, m ):
    if not hasattr( m, '_pass_structural_rtlir_gen' ):
      m._pass_structural_rtlir_gen = PassMetadata()
    for child in m.get_child_components():
      s.gen_metadata( child )

  # Override
  def gen_rtlir_types( s, m ):
    super().gen_rtlir_types( m )
    for child in m.get_child_components():
      s.gen_rtlir_types( child )

  # Override
  def gen_constants( s, m ):
    super().gen_constants( m )
    for child in m.get_child_components():
      s.gen_constants( child )

  # Override
  def sort_connections( s, m ):
    """Sort connections by the order `s.connect` is called.

    At L4 we need to recursively generate connections for every component.
    """
    super().sort_connections( m )

    for child in m.get_child_components():
      s.sort_connections( child )
