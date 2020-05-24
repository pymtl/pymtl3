#=========================================================================
# BehavioralTranslatorL5.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L5 behavioral translator."""

from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL5Pass import (
    BehavioralRTLIRGenL5Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL5Pass import (
    BehavioralRTLIRTypeCheckL5Pass,
)

from .BehavioralTranslatorL4 import BehavioralTranslatorL4


class BehavioralTranslatorL5( BehavioralTranslatorL4 ):
  def __init__( s, top ):
    super().__init__( top )

  def clear( s, tr_top ):
    super().clear( tr_top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL5Pass( s.tr_top ) )
    m.apply( BehavioralRTLIRTypeCheckL5Pass( s.tr_top ) )
    s.behavioral.rtlir[m] = \
        m.get_metadata( BehavioralRTLIRGenL5Pass.rtlir_upblks )
    s.behavioral.freevars[m] =\
        m.get_metadata( BehavioralRTLIRTypeCheckL5Pass.rtlir_freevars )
    s.behavioral.tmpvars[m] =\
        m.get_metadata( BehavioralRTLIRTypeCheckL5Pass.rtlir_tmpvars )

    # Visit the whole component hierarchy because now we have subcomponents
    for child in m.get_child_components(repr):
      s._gen_behavioral_trans_metadata( child )

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):
    super().translate_behavioral( m )
    for child in m.get_child_components(repr):
      s.translate_behavioral( child )
