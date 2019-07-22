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
  def __init__( s, top ):
    super().__init__( top )

  def clear( s, tr_top ):
    super().clear( tr_top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL4Pass() )
    m.apply( BehavioralRTLIRTypeCheckL4Pass() )
    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_freevars
    s.behavioral.tmpvars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
