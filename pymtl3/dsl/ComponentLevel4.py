"""
========================================================================
ComponentLevel4.py
========================================================================
We recognize methods and method call in update blocks. At this level
we only need CalleePort that contains actual method

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
from .ComponentLevel3 import ComponentLevel3
from .Connectable import BlockingIfc, MethodPort, NonBlockingIfc
from .ConstraintTypes import M, U
from .errors import UnmarkedUpdateOnceError
from .NamedObject import NamedObject


def update_once( blk ):
  NamedObject._elaborate_stack[-1]._update_once( blk )
  return blk

class ComponentLevel4( ComponentLevel3 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )

    inst._dsl.update_once = set()
    inst._dsl.M_constraints = set()

    # We don't want to get different objects everytime when we get a
    # method object from an instance. We do this by bounding the method
    # object to instance.

    # Shunning: After some profiling I found that getting dir(xxx) is
    # really slow so we would really like to avoid redundant calls to dir.
    # For example the previous code looks like this, which is REALLY bad.
    #
    # for name in dir(cls):
    #   if name in dir(ComponentLevel4)
    #
    # This means dir(ComponentLevel4) is called unnecessarily a huge
    # number of times.
    # Update: we should use cls.__dict__ to get all added methods!

    for name in cls.__dict__:
      if name[0] != '_': # filter private variables
        field = getattr( inst, name )
        if callable( field ):
          setattr( inst, name, field )

    return inst

  # Override
  def _collect_vars( s, m ):
    super()._collect_vars( m )
    if isinstance( m, ComponentLevel4 ):
      s._dsl.all_update_once   |= m._dsl.update_once
      s._dsl.all_M_constraints |= m._dsl.M_constraints

  def _check_upblk_calls( s ):
    all_update_once = s._dsl.all_update_once

    for blk, calls in s._dsl.all_upblk_calls.items():
      # if there is method call in normal update block we throw an error
      if blk not in all_update_once:
        method_calls = [ x for x in calls \
          if isinstance( x, (MethodPort, NonBlockingIfc, BlockingIfc)) ]
        if method_calls:
          raise UnmarkedUpdateOnceError( s._dsl.all_upblk_hostobj[ blk ], blk, method_calls )

  # Override
  def _check_valid_dsl_code( s ):
    s._check_upblk_writes()
    s._check_port_in_upblk()
    s._check_port_in_nets()
    s._check_upblk_calls()

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def _update_once( s, blk ):
    super()._update( blk )

    s._dsl.update_once.add( blk )
    s._cache_func_meta( blk, is_update_ff=True ) # add caching of src/ast

  # Override
  def add_constraints( s, *args ):
    super().add_constraints( *args )

    # add M-U, U-M, M-M constraints
    for (x0, x1, is_equal) in args:

      if   isinstance( x0, M ):
        assert isinstance( x1, (M, U) )
        s._dsl.M_constraints.add( (x0.func, x1.func, is_equal) )

      elif isinstance( x1, M ):
        assert isinstance( x0, U )
        s._dsl.M_constraints.add( (x0.func, x1.func, is_equal) )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()

    s._dsl.all_M_constraints = set()
    s._dsl.all_update_once = set()
