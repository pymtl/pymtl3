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
