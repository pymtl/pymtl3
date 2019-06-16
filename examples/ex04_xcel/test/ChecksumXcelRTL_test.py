
from __future__ import absolute_import, division, print_function

from pymtl3 import *

from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelCL_test import ChecksumXcelCLSrcSink_Tests as BaseTests

class XcelRTLSrcSink_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelRTL
