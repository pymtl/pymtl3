"""
========================================================================
ComponentLevel4.py
========================================================================
We recognize methods and method call in update blocks. At this level
we only need CalleePort that contains actual method

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
from __future__ import absolute_import, division, print_function

from .ComponentLevel3 import ComponentLevel3
from .Connectable import CalleePort, Signal
from .ConstraintTypes import M, U


class ComponentLevel4( ComponentLevel3 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel4, cls ).__new__( cls, *args, **kwargs )

    inst._dsl.M_constraints = set()

    # We don't want to get different objects everytime when we get a
    # method object from an instance. We do this by bounding the method
    # object to instance.
    for name in dir(cls):
      if name not in dir(ComponentLevel4) and not name.startswith("_") \
                                          and name != "line_trace":
        field = getattr( inst, name )
        if callable( field ):
          setattr( inst, name, field )

    return inst

  # Override
  def _declare_vars( s ):
    super( ComponentLevel4, s )._declare_vars()
    s._dsl.all_M_constraints = set()

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel4, s )._collect_vars( m )
    if isinstance( m, ComponentLevel4 ):
      s._dsl.all_M_constraints |= m._dsl.M_constraints

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def add_constraints( s, *args ):
    super( ComponentLevel4, s ).add_constraints( *args )

    # add M-U, U-M, M-M constraints
    for (x0, x1) in args:
      if   isinstance( x0, M ):
        if   isinstance( x1, U ):
          s._dsl.M_constraints.add( (x0.func, x1.func) )
        elif isinstance( x1, M ):
          s._dsl.M_constraints.add( (x0.func, x1.func) )
        else:
          assert False
      elif isinstance( x1, M ):
        if   isinstance( x0, U ):
          s._dsl.M_constraints.add( (x0.func, x1.func) )
        else:
          assert False
