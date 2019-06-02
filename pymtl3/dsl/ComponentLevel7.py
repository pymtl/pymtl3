"""
========================================================================
ComponentLevel7.py
========================================================================
Add functional-level blocking method decorator.

Author : Shunning Jiang
Date   : May 19, 2019
"""
from __future__ import absolute_import, division, print_function

from .ComponentLevel6 import ComponentLevel6

#-------------------------------------------------------------------------
# method_port decorator
#-------------------------------------------------------------------------

def blocking( method ):
  method._blocking = True
  return method

#-------------------------------------------------------------------------
# ComponentLevel7
#-------------------------------------------------------------------------

class ComponentLevel7( ComponentLevel6 ):

  def __new__( cls, *args, **kwargs ):

    inst = super( ComponentLevel7, cls ).__new__( cls, *args, **kwargs )

    inst._dsl.blocking_methods = set()

    for name in cls.__dict__:
      if not name.startswith("_"):
        method = getattr( inst, name )
        if hasattr( method, "_blocking" ):
          inst._dsl.blocking_methods.add( method )

    return inst

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel7, s )._collect_vars( m )
    if isinstance( m, ComponentLevel7 ):
      s._dsl.all_blocking_methods |= m._dsl.blocking_methods

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def _elaborate_declare_vars( s ):
    super( ComponentLevel7, s )._elaborate_declare_vars()

    s._dsl.all_blocking_methods = set()
