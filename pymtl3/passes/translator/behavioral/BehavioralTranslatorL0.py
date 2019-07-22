#=========================================================================
# BehavioralTranslatorL0.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L0 behavioral translator."""

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata


class BehavioralTranslatorL0( BaseRTLIRTranslator ):
  def __init__( s, top ):
    super().__init__( top )

  def clear( s, tr_top ):
    super().clear( tr_top )
    s.behavioral = TranslatorMetadata()

  def translate_behavioral( s, m ):
    pass
