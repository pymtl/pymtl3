#=========================================================================
# BehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L3 behavioral translator."""

from pymtl.passes.rtlir.behavioral.BehavioralRTLIRGenL3Pass\
    import BehavioralRTLIRGenL3Pass
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL3Pass\
    import BehavioralRTLIRTypeCheckL3Pass

from BehavioralTranslatorL2 import BehavioralTranslatorL2

class BehavioralTranslatorL3( BehavioralTranslatorL2 ):
  def __init__( s, top ):
    super( BehavioralTranslatorL3, s ).__init__( top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL3Pass() )
    m.apply( BehavioralRTLIRTypeCheckL3Pass() )
    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_freevars
    s.behavioral.tmpvars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
