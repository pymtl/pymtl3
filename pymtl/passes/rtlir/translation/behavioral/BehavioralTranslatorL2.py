#=========================================================================
# BehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L2 behavioral translator."""

from pymtl.passes.rtlir.behavioral.BehavioralRTLIRGenL2Pass\
    import BehavioralRTLIRGenL2Pass
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL2Pass\
    import BehavioralRTLIRTypeCheckL2Pass

from BehavioralTranslatorL1 import BehavioralTranslatorL1

class BehavioralTranslatorL2( BehavioralTranslatorL1 ):
  def __init__( s, top ):
    super( BehavioralTranslatorL2, s ).__init__( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_behavioral_trans_metadata( s, top ):
    s.behavioral.tmpvars = {}
    super( BehavioralTranslatorL2, s ).gen_behavioral_trans_metadata( top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL2Pass() )
    m.apply( BehavioralRTLIRTypeCheckL2Pass() )
    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_freevars
    s.behavioral.tmpvars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
