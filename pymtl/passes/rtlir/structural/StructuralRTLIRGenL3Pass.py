#=========================================================================
# StructuralRTLIRGenL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 3, 2019
"""Provide L3 structural RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

from ..RTLIRType import *
from .StructuralRTLIRGenL2Pass import StructuralRTLIRGenL2Pass
from .StructuralRTLIRSignalExpr import CurComp


class StructuralRTLIRGenL3Pass( StructuralRTLIRGenL2Pass ):

  def __call__( s, top ):

    super( StructuralRTLIRGenL3Pass, s ).__call__( top )
    s.gen_interfaces( top )

  def gen_interfaces( s, m ):
    """Collect all interfaces."""

  # Override
  def contains( s, obj, signal ):
    """Return if obj contains signal.
    
    At L3 not all signals have direct correspondance to `s.connect`
    statements because of interfaces. Therefore we need to check if `obj`
    is some parent of `signal`.
    """

    if obj == signal: return True

    while not isinstance( signal, CurComp ):
      if not hasattr( signal, 'get_base' ): return False
      signal = signal.get_base()
      if obj == signal:
        return True

    return False
