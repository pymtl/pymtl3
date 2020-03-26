#=========================================================================
# PlaceholderPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 27, 2020

from pymtl3 import MetadataKey, Placeholder
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PlaceholderConfigError


class PlaceholderPass( BasePass ):

  # Placeholder pass input pass data

  enable             = MetadataKey()
  has_clk            = MetadataKey()
  has_reset          = MetadataKey()

  # Placeholder pass output pass data

  placeholder_config = MetadataKey()

  def __call__( s, m ):
    if isinstance( m, Placeholder ):
      s.visit_placeholder( m )
    for child in m.get_child_components(repr):
      s.__call__( child )

  def visit_placeholder( s, m ):
    s.setup_configs( m )

  def setup_configs( s, m ):
    c = s.__class__
    ph_config = c.get_placeholder_config()( m )
    m.set_metadata( c.placeholder_config, ph_config )

  @staticmethod
  def get_placeholder_config():
    from pymtl3.passes.PlaceholderConfigs import PlaceholderConfigs
    return PlaceholderConfigs
