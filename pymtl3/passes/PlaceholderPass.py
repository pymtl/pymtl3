#=========================================================================
# PlaceholderPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 27, 2020

from pymtl3 import Placeholder
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PlaceholderConfigError


class PlaceholderPass( BasePass ):

  def __call__( s, m ):
    if not isinstance(m, Placeholder) and hasattr(m, 'config_placeholder'):
      raise PlaceholderConfigError(m,
          "the given object is not a Placeholder but has `config_placeholder` attribute!")

    if isinstance( m, Placeholder ):
      s.visit_placeholder( m )
    for child in m.get_child_components(repr):
      s.__call__( child )

  def visit_placeholder( s, m ):
    if not hasattr( m, '_placeholder_meta' ):
      m._placeholder_meta = PassMetadata()
