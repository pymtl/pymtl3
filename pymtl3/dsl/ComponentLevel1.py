"""
========================================================================
ComponentLevel1.py
========================================================================
At the bottom level, we only have update blocks and explicit constraints
between two update blocks/one update block. Basically this layer defines
the scheduling policy/elaboration process.
Each update block is called exactly once every cycle. PyMTL will
schedule all update blocks based on the constraints. A total constraint
between two update blocks specifies the order of the two blocks, i.e.
call A before B.
We collect one type of explicit constraints at this level:
* Block constraint: s.add_constraints( U(upA) < U(upB) )

Author : Shunning Jiang
Date   : Nov 3, 2018
"""
from __future__ import absolute_import, division, print_function

import re

from .ConstraintTypes import U
from .errors import NotElaboratedError, UpblkFuncSameNameError
from .NamedObject import NamedObject

p = re.compile('( *((@|def).*))')

class ComponentLevel1( NamedObject ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    """ Convention: variables local to the object is created in __new__ """

    inst = super( ComponentLevel1, cls ).__new__( cls, *args, **kwargs )

    inst._dsl.name_upblk = {}
    inst._dsl.upblks     = set()
    inst._dsl.U_U_constraints = set() # contains ( id(func), id(func) )s

    return inst

  def _declare_vars( s ):
    """ Convention: the top level component on which we call elaborate
    declare variables in _declare_vars; it shouldn't have them before
    elaboration.

    Convention: the variables that hold all metadata of descendants
    should have _all prefix."""

    s._dsl.all_upblks = set()
    s._dsl.all_upblk_hostobj = {}
    s._dsl.all_U_U_constraints = set()

  def _collect_vars( s, m ):
    """ Called on individual objects during elaboration.
    The general format resembles "s._all_X.update/append( s._X ). """

    if isinstance( m, ComponentLevel1 ):
      s._dsl.all_upblks |= m._dsl.upblks
      for blk in m._dsl.upblks:
        s._dsl.all_upblk_hostobj[ blk ] = m
      s._dsl.all_U_U_constraints |= m._dsl.U_U_constraints

  def _uncollect_vars( s, m ):

    if isinstance( m, ComponentLevel1 ):
      s._dsl.all_upblks -= m._dsl.upblks
      for k in m._dsl.upblks:
        del s._dsl.all_upblk_hostobj[ k ]
      s._dsl.all_U_U_constraints -= m._dsl.U_U_constraints

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def update( s, blk ):
    name = blk.__name__
    if name in s._dsl.name_upblk:
      raise UpblkFuncSameNameError( name )

    s._dsl.name_upblk[ name ] = blk
    s._dsl.upblks.add( blk )
    return blk

  def add_constraints( s, *args ):
    for (x0, x1, is_equal) in args:
      assert is_equal == False
      assert isinstance( x0, U ) and isinstance( x1, U ), "Only accept up1<up2"
      assert (x0.func, x1.func) not in s._dsl.U_U_constraints, \
        "Duplicated constraint"
      s._dsl.U_U_constraints.add( (x0.func, x1.func) )

  def construct( s, *args, **kwargs ):
    raise NotImplementedError("construct method, where the design is built,"
                              " is not implemented in {}".format( s.__class__.__name__ ) )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  def elaborate( s ):
    # Directly use the base class elaborate
    NamedObject.elaborate( s )

    s._declare_vars()
    for c in s._dsl.all_named_objects:
      if isinstance( c, ComponentLevel1 ):
        s._collect_vars( c )

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def is_component( s ):
    return True

  def is_signal( s ):
    return False

  def is_interface( s ):
    return False

  def get_update_block( s, name ):
    return s._dsl.name_upblk[ name ]

  def get_update_block_host_component( s, blk ):
    try:
      assert s._dsl.elaborate_top is s, "Getting update block host component " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_upblk_hostobj[ blk ]
    except AttributeError:
      raise NotElaboratedError()

  def get_update_blocks( s ):
    return s._dsl.upblks

  def get_all_update_blocks( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all update blocks " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_upblks
    except AttributeError:
      raise NotElaboratedError()

  def get_component_level( s ):
    try:
      return s._dsl.level
    except AttributeError:
      raise NotElaboratedError()

  def get_all_explicit_constraints( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all explicit constraints " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_U_U_constraints
    except AttributeError:
      raise NotElaboratedError()

  def get_child_components( s ):
    assert s._dsl.constructed
    ret = set()
    stack = []
    for (name, obj) in s.__dict__.iteritems():
      if   isinstance( name, basestring ): # python2 specific
        if not name.startswith("_"): # filter private variables
          stack.append( obj )
    while stack:
      u = stack.pop()
      if   isinstance( u, ComponentLevel1 ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret

  def get_all_components( s ):
    try:
      return s._dsl.all_components
    except AttributeError:
      return s._collect_all( lambda x: isinstance( x, ComponentLevel1 ) )

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    try:
      return set( [ x for x in s._dsl.all_components if filt(x) ] )
    except AttributeError:
      return s._collect_all( filt )

  def delete_component_by_name( s, name ):

    # This nested delete function is to create an extra layer to properly
    # call garbage collector. If we can make sure it is collected
    # automatically and fast enough, we might remove this extra layer
    #
    # EDIT: After experimented w/ and w/o gc.collect(), it seems like it
    # is eventually collected, but sometimes the intermediate memory
    # footprint might reach up to gigabytes, so let's keep the
    # gc.collect() for now

    def _delete_component_by_name( parent, name ):
      obj = getattr( parent, name )
      top = s._dsl.elaborate_top

      # Remove all components and uncollect metadata

      removed_components = obj.get_all_components()
      top._dsl.all_components -= removed_components

      for x in removed_components:
        assert x._dsl.elaborate_top is top
        top._uncollect_vars( x )

      for x in obj._collect_all():
        del x._dsl.parent_obj

      delattr( s, name )

    _delete_component_by_name( s, name )
    import gc
    gc.collect()

  def add_component_by_name( s, name, obj ):
    assert not hasattr( s, name )
    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
    setattr( s, name, obj )
    del NamedObject.__setattr__

    top = s._dsl.elaborate_top

    added_components = obj.get_all_components()
    top._dsl.all_components |= added_components

    for c in added_components:
      c._dsl.elaborate_top = top
      top._collect_vars( c )

  def apply( s, *args ):

    if isinstance(args[0], list):
      assert len(args) == 1
      for step in args[0]:
        step( s )

    elif len(args) == 1:
      assert callable( args[0] )
      args[0]( s )
