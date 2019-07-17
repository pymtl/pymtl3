"""
==========================================================================
utils.py
==========================================================================
Utilities for PyH2.

Author : Yanghui Ou, Yixiao Zhang
  Date : July 10, 2019
"""
from __future__ import absolute_import, division, print_function

import attr
import hypothesis.strategies as st

from pymtl3 import *

#-------------------------------------------------------------------------
# Method
#-------------------------------------------------------------------------
# Metadata for method spec.

@attr.s()
class Method( object ):
  method_name = attr.ib()
  args = attr.ib( default={} )
  rets = attr.ib( default={} )

#-------------------------------------------------------------------------
# rename
#-------------------------------------------------------------------------
# A decorator that renames a function.

def rename( name ):
  def wrap( f ):
    f.__name__ = name
    return f
  return wrap

#-------------------------------------------------------------------------
# list_string
#-------------------------------------------------------------------------

def list_string( lst ):
  return ", ".join([ str( x ) for x in lst ] )

#-------------------------------------------------------------------------
# kwarg_to_str
#-------------------------------------------------------------------------

def kwarg_to_str( kwargs ):
  return list_string(
      [ "{k}={v}".format( k=k, v=v ) for k, v in kwargs.items() ] )

#-------------------------------------------------------------------------
# pyh2_line_trace
#-------------------------------------------------------------------------

def method_to_str( self ):
  # TODO : figure out trace len more smartly
  trace_len = 20
  if self.method.called and self.rdy.called and self.rdy.saved_ret:
    kwargs_str = kwarg_to_str( self.method.saved_kwargs )
    ret_str = (
      "" if self.method.saved_ret is None else
      " -> " + str( self.method.saved_ret )
    )
    return "{name}({kwargs}){ret}".format(
      name=self._dsl.my_name,
      kwargs=kwargs_str,
      ret=ret_str
    ).ljust( trace_len )
  elif self.rdy.called:
    if self.rdy.saved_ret:
      return " ".ljust( trace_len )
    else:
      return "#".ljust( trace_len )
  elif not self.rdy.called:
    return ".".ljust( trace_len )
  return "X".ljust( trace_len )