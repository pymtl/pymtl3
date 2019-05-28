#=========================================================================
# errors.py
#=========================================================================
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 4, 2019
"""Behavioral code errors."""

from __future__ import absolute_import, division, print_function

import inspect
import os
import sys
import traceback


class RTLIRConversionError( Exception ):
  """Error while converting a PyMTL structure into RTLIR."""
  def __init__( self, obj, msg ):
    obj = str(obj)
    _, _, tb = sys.exc_info()
    traceback.print_tb(tb)
    tb_info = traceback.extract_tb(tb)
    fname, line, func, text = tb_info[-1]
    return super( RTLIRConversionError, self ).__init__(
      "\nIn file {fname}, Line {line}, Method {func}:"
      "\nError trying to convert {obj} into RTLIR:\n- {msg}"
      "\n  {text}".format( **locals() ) )

class PyMTLSyntaxError( Exception ):
  """Behavioral RTLIR syntax error."""
  def __init__( self, blk, ast, msg ):
    fname = os.path.abspath( inspect.getsourcefile( blk ) )
    line = inspect.getsourcelines( blk )[1]
    col = 0
    code = ""
    try:
      line += ast.lineno - 1
      col = ast.col_offset
      code_line = inspect.getsourcelines( blk )[0][ ast.lineno-1 ]
      code = '\n  ' + code_line.strip() + \
        '\n  '+ ' ' * (col-len(code_line)+len(code_line.lstrip())) + '^'
    except AttributeError:
      # The given AST node is neither expr nor stmt
      pass
    return super( PyMTLSyntaxError, self ).__init__(
      "\nIn file {fname}, Line {line}, Col {col}:{code}\n- {msg}". \
      format( **locals() )
    )

class PyMTLTypeError( Exception ):
  """Behavioral RTLIR type error."""
  def __init__( self, blk, ast, msg ):
    fname = os.path.abspath( inspect.getsourcefile( blk ) )
    line = inspect.getsourcelines( blk )[1]
    col = 0
    code = ""
    try:
      line += ast.lineno - 1
      col = ast.col_offset
      code_line = inspect.getsourcelines( blk )[0][ ast.lineno-1 ]
      code = '\n  ' + code_line.strip() + \
        '\n  '+ ' ' * (col-len(code_line)+len(code_line.lstrip())) + '^'
    except AttributeError:
      # The given AST node is neither expr nor stmt
      pass
    return super( PyMTLTypeError, self ).__init__(
      "\nIn file {fname}, Line {line}, Col {col}:{code}\n- {msg}". \
      format( **locals() )
    )
