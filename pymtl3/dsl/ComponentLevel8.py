"""
========================================================================
ComponentLevel8.py
========================================================================
We recognize methods and method call in update blocks. At this level
we only need CalleePort that contains actual method

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
import ast

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel7 import ComponentLevel7
from .NamedObject import NamedObject


def update_delay( delay ):
  def real_decorator( blk ):
    NamedObject._elaborate_stack[-1]._update_delay( blk, delay )
    return blk
  return real_decorator

class ComponentLevel8( ComponentLevel7 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )

    inst._dsl.update_delay = {}
    return inst

  # Override
  def _collect_vars( s, m ):
    super()._collect_vars( m )
    if isinstance( m, ComponentLevel8 ):
      s._dsl.all_update_delay.update( m._dsl.update_delay )

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def _update_delay( s, blk, delay ):
    ComponentLevel1._update( s, blk )

    s._dsl.update_delay[ blk ] = delay
    s._cache_func_meta( blk, 4, ast.BitOr ) # add caching of src/ast


  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()

    s._dsl.all_update_delay = {}
    s._dsl.all_update_once = set()
