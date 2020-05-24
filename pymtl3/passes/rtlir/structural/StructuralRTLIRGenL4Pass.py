#=========================================================================
# StructuralRTLIRGenL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Apr 3, 2019
"""Provide L4 structural RTLIR generation pass."""

from .StructuralRTLIRGenL3Pass import StructuralRTLIRGenL3Pass


class StructuralRTLIRGenL4Pass( StructuralRTLIRGenL3Pass ):
  """At L4 we need to recursively generate metadata for every component"""

  # Override
  def _gen_metadata( s, m ):
    super()._gen_metadata( m )
    for child in m.get_child_components(repr):
      s._gen_metadata( child )
