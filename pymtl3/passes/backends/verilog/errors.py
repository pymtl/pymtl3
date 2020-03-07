#=========================================================================
# errors.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Exception classes for SystemVerilog backend."""

import inspect
import os
import sys
import traceback


class VerilogImportError( Exception ):
  """Error while performing import."""
  def __init__( self, obj, msg ):
    obj = str(obj)
    _, _, tb = sys.exc_info()

    if not tb:
      # There are no chaining exceptions
      return super().__init__(
        f"\nError trying to perform import on {obj}:\n- {msg}")
    else:
      # There is another cause for the current import error
      tb_info = traceback.extract_tb(tb)
      fname, line, func, _ = tb_info[-1]
      return super().__init__(
        f"\nIn file {fname}, Line {line}, Method {func}:"
        f"\nError trying to perform import on {obj}:\n- {msg}")

class VerilogTranslationError( Exception ):
  """SystemVerilog translation error."""
  def __init__( self, blk, _ast, msg ):
    ast = _ast.ast
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
    return super().__init__(
      f"\nIn file {fname}, Line {line}, Col {col}:{code}\n- {msg}" )

class VerilogStructuralTranslationError( Exception ):
  """SystemVerilog translation error."""
  def __init__( self, obj, msg ):
    return super().__init__(
      f"\nError while performing structural translation on {obj}\n- {msg}" )

class VerilogReservedKeywordError( Exception ):
  """SystemVerilog reserved keyword error."""
  def __init__( self, name, msg ):
    return super().__init__(
      f"- {name} is a SystemVerilog reserved keyword!\n- {msg}" )

class VerilogCloseLoopPurePythonSimError( Exception ):
  """SystemVerilog closed loop test error during pure python simulation."""
  def __init__( self, obj, msg ):
    return super().__init__(
      f"\nCalling closed-loop test method with component {obj}:\n- {msg}" )

class VerilogPlaceholderError( Exception ):
  """SystemVerilog placeholder error."""
  def __init__( self, obj, msg ):
    return super().__init__(
      f"\nError while pickling placeholder {obj}:\n- {msg}" )
