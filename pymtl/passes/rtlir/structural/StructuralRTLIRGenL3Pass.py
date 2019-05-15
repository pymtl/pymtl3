#=========================================================================
# StructuralRTLIRGenL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 3, 2019
"""Provide L3 structural RTLIR generation pass."""

from StructuralRTLIRGenL2Pass import StructuralRTLIRGenL2Pass
from ..RTLIRType import *
from StructuralRTLIRSignalExpr import CurComp

class StructuralRTLIRGenL3Pass( StructuralRTLIRGenL2Pass ):

  def __call__( s, top ):

    super( StructuralRTLIRGenL3Pass, s ).__call__( top )
    s.gen_interfaces( top )

  def gen_interfaces( s, m ):
    """
       Collect all interfaces to generate their definitions later.
    """

    # ns = s.top._pass_structural_rtlir_gen
    # if not hasattr( ns, 'ifcs' ): ns.ifcs = []
    # m_rtype = ns.rtlir_type

    # for name, ifc_rtype in m_rtype.get_ifc_views():
      # ifc_name = ifc_rtype.get_name()
      # if not ifc_name in map( lambda x: x[0], ns.ifcs ):
        # ns.ifcs.append( ( ifc_name, ifc_rtype ) )

  #-----------------------------------------------------------------------
  # contains
  #-----------------------------------------------------------------------
  # At L3 not all signals have direct correspondance to `s.connect`
  # statements because of interfaces. Therefore we need to check if `obj`
  # is some parent of `signal`.

  # Override
  def contains( s, obj, signal ):

    if obj == signal: return True

    while not isinstance( signal, CurComp ):
      if not hasattr( signal, 'get_base' ): return False
      signal = signal.get_base()
      if obj == signal:
        return True

    return False
