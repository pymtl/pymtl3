#=========================================================================
# StructuralRTLIRGenL0Pass.py
#=========================================================================

from pymtl3 import MetadataKey
from pymtl3.passes.rtlir.RTLIRPass import RTLIRPass


class StructuralRTLIRGenL0Pass( RTLIRPass ):

  # Pass metadata

  #: RTLIR type of the component
  #:
  #: Type: ``RTLIRType.Component``; output
  rtlir_type = MetadataKey()

  #: RTLIR of all constants that belong to the component
  #:
  #: Type: ``list``; output
  consts = MetadataKey()

  #: RTLIR of all connections in component
  #:
  #: Type: ``list``; output
  connections = MetadataKey()
