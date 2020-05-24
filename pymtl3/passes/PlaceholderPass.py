#=========================================================================
# PlaceholderPass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 27, 2020

from pymtl3 import MetadataKey, Placeholder

from .BasePass import BasePass
from .errors import PlaceholderConfigError


class PlaceholderPass( BasePass ):

  # Placeholder pass input pass data

  #: Enable pickling on the placeholder component.
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  enable             = MetadataKey(bool)

  #: Does the module of external source have clk pin?
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  has_clk            = MetadataKey(bool)

  #: Does the module of external source have reset pin?
  #:
  #: Type: ``bool``; input
  #:
  #: Default value: ``False``
  has_reset          = MetadataKey(bool)

  # Placeholder pass output pass data

  #: An instance of :class:`PlaceholderConfigs` that contains the parsed options.
  #:
  #: Type: ``PlaceholderConfigs``; output
  placeholder_config = MetadataKey()

  def __call__( s, m ):
    """Pickle every ``Placeholder`` in the component hierarchy rooted at ``m``."""
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
