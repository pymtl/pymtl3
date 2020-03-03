#=========================================================================
# PlaceholderPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 27, 2020

from pymtl3 import Placeholder
from pymtl3.passes.BasePass import BasePass, PassMetadata


class PlaceholderPass( BasePass ):

  def __call__( s, m ):
    if isinstance( m, Placeholder ):
      s.visit_placeholder( m )
    for child in m.get_child_components():
      s.__call__( child )

  def visit_placeholder( s, m ):
    if not hasattr( m, '_placeholder_meta' ):
      m._placeholder_meta = PassMetadata()
