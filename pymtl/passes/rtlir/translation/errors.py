#=========================================================================
# errors.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide exception types for translation errors."""
from __future__ import absolute_import, division, print_function


class RTLIRTranslationError( Exception ):
  """Exception type for errors happening during translation of RTLIR."""
  def __init__( self, obj, msg ):
    obj = str(obj)
    return super(RTLIRTranslationError, self).__init__(
        "\nError trying to translate top component {obj}:\n- {msg}". \
        format(**locals()))
