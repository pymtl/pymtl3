#=========================================================================
# BaseRTLIRTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 11, 2019
"""Provide base class and metadata namespace for RTLIR translators."""


class BaseRTLIRTranslator:
  """Base class of RTLIR translators."""

  def __init__( s, top ):
    s.top = top

  def clear( s, tr_top ):
    s.tr_top = tr_top
    s.component = {}
    s.hierarchy = TranslatorMetadata()
    s.gen_base_rtlir_trans_metadata( s.tr_top )

  def gen_base_rtlir_trans_metadata( s, m ):
    s.component[m] = TranslatorMetadata()
    for child in m.get_child_components(repr):
      s.gen_base_rtlir_trans_metadata( child )

#-------------------------------------------------------------------------
# TranslatorMetadata
#-------------------------------------------------------------------------

class TranslatorMetadata:
  """Metadata namespace used by RTLIR translators."""
  def __init__( s ):
    pass
