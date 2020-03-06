#=========================================================================
# errors.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide exception types for translation errors."""

import sys
import traceback


class RTLIRTranslationError( Exception ):
  """Exception type for errors happening during translation of RTLIR."""
  def __init__( self, obj, msg ):
    obj = str(obj)
    _, _, tb = sys.exc_info()
    tb_info = traceback.extract_tb(tb)
    fname, line, func, text = tb_info[-1]
    return super().__init__(
      f"\nIn file {fname}, Line {line}, Method {func}:"
      f"\nError trying to translate top component {obj}:\n- {msg}"
      f"\n  {text}" )
