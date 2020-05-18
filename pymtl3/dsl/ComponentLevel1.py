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
import re

from .ConstraintTypes import U
from .errors import InvalidPlaceholderError, NotElaboratedError, UpblkFuncSameNameError
from .NamedObject import NamedObject
from .Placeholder import Placeholder

p = re.compile('( *((@|def).*))')

def update( blk ):
  NamedObject._elaborate_stack[-1]._update( blk )
  return blk

class ComponentLevel1( NamedObject ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    """ Convention: variables local to the object is created in __new__ """

    inst = super().__new__( cls, *args, **kwargs )

    inst._dsl.name_upblk  = {}
    inst._dsl.upblks      = set()
    inst._dsl.upblk_order = []
    inst._dsl.U_U_constraints = set() # contains ( id(func), id(func) )s

    return inst

  def _collect_vars( s, m ):
    """ Called on individual objects during elaboration/addcomponent.
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

  def _update( s, blk ):
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot define update block <{}> "
              "in a placeholder component.".format( blk.__name__ ) )
    name = blk.__name__
    if name in s._dsl.name_upblk:
      raise UpblkFuncSameNameError( name )

    s._dsl.name_upblk[ name ] = blk
    s._dsl.upblks.add( blk )
    s._dsl.upblk_order.append( blk )

  def get_update_block( s, name ):
    return s._dsl.name_upblk[ name ]

  def add_constraints( s, *args ):
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot define constraints {}"
              "in a placeholder component.".format( blk.__name__ ) )
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

  # We refactor the monolithic elaborate function into smaller functions

  def _elaborate_declare_vars( s ):
    """ Convention: the top level component on which we call elaborate
    declare variables in _declare_vars; it shouldn't have them before
    elaboration.

    Convention: the variables that hold all metadata of descendants
    should have _all prefix."""

    s._dsl.all_upblks = set()
    s._dsl.all_upblk_hostobj = {}
    s._dsl.all_U_U_constraints = set()

    # Although this all_components is a subset of all_named_objects in
    # NamedObject class, I still maintain it here because we want to avoid
    # redundant isinstance check. This being said, I'm going to pay the
    # extra cost of removing from both all_named_objects and this
    # all_components when I delete a component
    s._dsl.all_components = set()

  def _elaborate_collect_all_vars( s ):
    for c in s._dsl.all_named_objects:
      if isinstance( c, ComponentLevel1 ):
        s._dsl.all_components.add( c )
        s._collect_vars( c )

  def elaborate( s ):
    # Directly use the base class elaborate
    NamedObject.elaborate( s )

    s._elaborate_declare_vars()
    s._elaborate_collect_all_vars()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------

  def is_component( s ):
    return True

  def is_signal( s ):
    return False

  def is_interface( s ):
    return False
