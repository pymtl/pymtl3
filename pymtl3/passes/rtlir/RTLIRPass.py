#=========================================================================
# RTLIRPass.py
#=========================================================================
# Provides the rtlir_getter metadata key.
#
# Author : Peitian Pan
# Date   : May 17, 2020

from pymtl3 import MetadataKey
from pymtl3.passes.BasePass import BasePass


class RTLIRPass( BasePass ):

  #: An RTLIR getter
  #:
  #: Type: ``RTLIRGetter``; output
  rtlir_getter = MetadataKey()
