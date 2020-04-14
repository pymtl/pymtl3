#=========================================================================
# BehavioralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L4 behavioral translator."""

from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL4Pass import (
    BehavioralRTLIRGenL4Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL4Pass import (
    BehavioralRTLIRTypeCheckL4Pass,
)

from .BehavioralTranslatorL3 import BehavioralTranslatorL3


class BehavioralTranslatorL4( BehavioralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL4Pass( s.tr_top ) )
    m.apply( BehavioralRTLIRTypeCheckL4Pass( s.tr_top ) )
    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_freevars
    s.behavioral.tmpvars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
