#=========================================================================
# errors.py
#=========================================================================
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 4, 2019

import os, inspect

class PyMTLSyntaxError( Exception ):
  """ Raise error when the RAST generation pass finds a syntax error """
  def __init__( self, blk, ast, msg ):
    fname = os.path.abspath( inspect.getsourcefile( blk ) )
    line = inspect.getsourcelines( blk )[1]
    col = 0
    code = ""

    try:
      line += ast.lineno - 1
      col = ast.col_offset
      code_line = inspect.getsourcelines( blk )[0][ ast.lineno-1 ]
      code = '\n  ' + code_line.strip() +\
        '\n  '+ ' ' * (col-len(code_line)+len(code_line.lstrip())) + '^'
    except AttributeError:
      # The given AST node is not expr nor stmt
      pass

    return super( PyMTLSyntaxError, self ).__init__(
      "File {fname}, Line {line}, Col {col}:{code}\n- {msg}".\
      format( **locals() ) 
    )

class PyMTLTypeError( Exception ):
  """ Raise error when the RAST type check pass finds an error """
  def __init__( self, blk, ast, msg ):
    fname = os.path.abspath( inspect.getsourcefile( blk ) )
    line = inspect.getsourcelines( blk )[1]
    col = 0
    code = ""

    try:
      line += ast.lineno - 1
      col = ast.col_offset
      code_line = inspect.getsourcelines( blk )[0][ ast.lineno-1 ]
      code = '\n  ' + code_line.strip() +\
        '\n  '+ ' ' * (col-len(code_line)+len(code_line.lstrip())) + '^'
    except AttributeError:
      # The given AST node is not expr nor stmt
      pass

    return super( PyMTLTypeError, self ).__init__(
      "File {fname}, Line {line}, Col {col}:{code}\n- {msg}".\
      format( **locals() ) 
    )

