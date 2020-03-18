#=========================================================================
# PlaceholderPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 27, 2020

from pymtl3 import Placeholder
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PlaceholderConfigError
from pymtl3.passes.PassDataName import PassDataName


class PlaceholderPass( BasePass ):

  # Placeholder pass input pass data

  enable             = PassDataName()
  has_clk            = PassDataName()
  has_reset          = PassDataName()

  # Placeholder pass output pass data

  placeholder_config = PassDataName()

  def __call__( s, m ):
    if isinstance( m, Placeholder ):
      s.visit_placeholder( m )
    for child in m.get_child_components():
      s.__call__( child )

  def visit_placeholder( s, m ):
    s.setup_configs( m )

  def setup_configs( s, m ):
    c = s.__class__
    ph_config = c.get_placeholder_config()( m )
    m.set_pass_data( c.placeholder_config, ph_config )

  @staticmethod
  def get_placeholder_config():
    from pymtl3.passes.PlaceholderConfigs import PlaceholderConfigs
    return PlaceholderConfigs
