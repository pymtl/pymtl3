#=========================================================================
# BehavioralTranslatorL0.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L0 behavioral translator."""

from __future__ import absolute_import, division, print_function

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata


class BehavioralTranslatorL0( BaseRTLIRTranslator ):
  def __init__( s, top ):
    super( BehavioralTranslatorL0, s ).__init__( top )

  def clear( s, tr_top ):
    super( BehavioralTranslatorL0, s ).clear( tr_top )
    s.behavioral = TranslatorMetadata()

  def translate_behavioral( s, m ):
    pass
