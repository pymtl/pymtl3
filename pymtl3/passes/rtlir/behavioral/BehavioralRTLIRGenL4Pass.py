#=========================================================================
# BehavioralRTLIRGenL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L4 behavioral RTLIR generation pass."""

from .BehavioralRTLIRGenL3Pass import (
    BehavioralRTLIRGeneratorL3,
    BehavioralRTLIRGenL3Pass,
)


class BehavioralRTLIRGenL4Pass( BehavioralRTLIRGenL3Pass ):
  # Override
  def get_rtlir_generator_class( s ):
    return BehavioralRTLIRGeneratorL4

class BehavioralRTLIRGeneratorL4( BehavioralRTLIRGeneratorL3 ):
  """Behavioral RTLIR generator level 4.

  Do nothing here because attributes have been handled in previous
  levels.
  """
