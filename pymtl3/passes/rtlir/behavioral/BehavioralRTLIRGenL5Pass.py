#=========================================================================
# BehavioralRTLIRGenL5Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L5 behavioral RTLIR generation pass."""

from .BehavioralRTLIRGenL4Pass import (
    BehavioralRTLIRGeneratorL4,
    BehavioralRTLIRGenL4Pass,
)


class BehavioralRTLIRGenL5Pass( BehavioralRTLIRGenL4Pass ):
  # Override
  def get_rtlir_generator_class( s ):
    return BehavioralRTLIRGeneratorL5

class BehavioralRTLIRGeneratorL5( BehavioralRTLIRGeneratorL4 ):
  """Behavioral RTLIR generator level 5.

  Do nothing here because attributes have been handled in previous
  levels.
  """
