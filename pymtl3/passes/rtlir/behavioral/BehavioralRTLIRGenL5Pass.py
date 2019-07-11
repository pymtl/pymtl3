#=========================================================================
# BehavioralRTLIRGenL5Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L5 behavioral RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.BasePass import BasePass, PassMetadata

from .BehavioralRTLIRGenL4Pass import BehavioralRTLIRGeneratorL4


class BehavioralRTLIRGenL5Pass( BasePass ):
  def __call__( s, m ):
    """Generate RTLIR for all upblks of m."""
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()
    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL5( m )
    upblks = {
      'CombUpblk' : list(m.get_update_blocks() - m.get_update_on_edge()),
      'SeqUpblk'  : list(m.get_update_on_edge())
    }
    # Sort the upblks by their name
    upblks['CombUpblk'].sort( key = lambda x: x.__name__ )
    upblks['SeqUpblk'].sort( key = lambda x: x.__name__ )

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = \
          visitor.enter( blk, m.get_update_block_ast( blk ) )

class BehavioralRTLIRGeneratorL5( BehavioralRTLIRGeneratorL4 ):
  """Behavioral RTLIR generator level 5.

  Do nothing here because attributes have been handled in previous
  levels.
  """
  def __init__( s, component ):
    super( BehavioralRTLIRGeneratorL5, s ).__init__( component )
