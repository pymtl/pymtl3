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
