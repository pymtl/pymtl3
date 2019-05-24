#=========================================================================
# BaseRTLIRTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 11, 2019
"""Provide base class and metadata namespace for RTLIR translators."""
from __future__ import absolute_import, division, print_function


class BaseRTLIRTranslator( object ):
  """Base class of RTLIR translators."""

  def __init__( s, top ):
    s.top = top
    s.component = {}
    s.hierarchy = TranslatorMetadata()
    s.gen_base_rtlir_trans_metadata( s.top )

  def gen_base_rtlir_trans_metadata( s, m ):
    s.component[m] = TranslatorMetadata()
    for child in m.get_child_components():
      s.gen_base_rtlir_trans_metadata( child )

#-------------------------------------------------------------------------
# TranslatorMetadata
#-------------------------------------------------------------------------

class TranslatorMetadata( object ):
  """Metadata namespace used by RTLIR translators."""
  def __init__( s ):
    pass
