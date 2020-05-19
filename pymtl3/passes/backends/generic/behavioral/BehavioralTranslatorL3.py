#=========================================================================
# BehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L3 behavioral translator."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL3Pass import (
    BehavioralRTLIRGenL3Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL3Pass import (
    BehavioralRTLIRTypeCheckL3Pass,
)

from .BehavioralTranslatorL2 import BehavioralTranslatorL2


class BehavioralTranslatorL3( BehavioralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL3Pass( s.tr_top ) )
    m.apply( BehavioralRTLIRTypeCheckL3Pass( s.tr_top ) )
    s.behavioral.rtlir[m] = \
        m.get_metadata( BehavioralRTLIRGenL3Pass.rtlir_upblks )
    s.behavioral.freevars[m] =\
        m.get_metadata( BehavioralRTLIRTypeCheckL3Pass.rtlir_freevars )
    s.behavioral.tmpvars[m] =\
        m.get_metadata( BehavioralRTLIRTypeCheckL3Pass.rtlir_tmpvars )

  #-----------------------------------------------------------------------
  # Freevar datatype dispatch
  #-----------------------------------------------------------------------

  def dispatch_freevar_datatype( s, dtype ):
    if isinstance( dtype, rdt.Struct ):
      return s.rtlir_tr_struct_dtype( dtype )
    else:
      return super().dispatch_freevar_datatype( dtype )
