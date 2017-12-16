#=========================================================================
# ComponentLevel1.py
#=========================================================================
# At the bottom level, we only have update blocks and explicit constraints
# between two update blocks/one update block. Basically this layer defines
# the scheduling policy/elaboration process.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# call A before B.
# We collect one type of explicit constraints at this level:
# * Block constraint: s.add_constraints( U(upA) < U(upB) )

from NamedObject     import NamedObject
from ConstraintTypes import U
from errors          import UpblkFuncSameNameError
from pymtl.datatypes import *

import inspect2, re, ast, py
p = re.compile('( *((@|def).*))')

class ComponentLevel1( NamedObject ):

  def __new__( cls, *args, **kwargs ):
    """ Convention: variables local to the object is created in __new__ """

    inst = super( ComponentLevel1, cls ).__new__( cls, *args, **kwargs )

    inst._name_upblk = {}
    inst._U_U_constraints = set() # contains ( id(func), id(func) )s

    return inst

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      assert isinstance( x0, U ) and isinstance( x1, U ), "Only accept up1<up2"
      s._U_U_constraints.add( (x0.func, x1.func) )

  def update( s, blk ):
    name = blk.__name__
    if name in s._name_upblk:
      raise UpblkFuncSameNameError( name )

    s._name_upblk[ name ] = blk
    blk.hostobj = s
    return blk

  def compile_update_block( s, src ): # FIXME
    var = locals()
    var.update( globals() ) # the src may have Bits
    exec py.code.Source( src ).compile() in var
    s.record_update_block( blk )
    return blk

  # These functions are called during elaboration and should be overriden,
  # but remember to call super method whenever necessary.

  def elaborate( s ):
    """ Elaboration steps. Child classes should override and rewrite it. """

    s._declare_vars()
    s._tag_name_collect()

    for obj in s._pymtl_objs:
      assert isinstance( obj, ComponentLevel1 ) # just component
      s._collect_vars( obj )

  def _declare_vars( s ):
    """ Convention: the component on which we call elaborate declare
    variables in _declare_vars; it shouldn't have them before elaboration.

    Convention: the variables that hold all metadata of descendants
    should have _all prefix."""

    s._all_upblks = set()
    s._all_U_U_constraints = set()

  def _collect_vars( s, m ):
    """ Called on individual objects during elaboration.
    The general format resembles "s._all_X.update/append( s._X ). """

    if isinstance( m, ComponentLevel1 ):
      s._all_upblks.update( m._name_upblk.values() )
      s._all_U_U_constraints.update( m._U_U_constraints )

  def get_update_block( s, name ):
    return s._name_upblk[ name ]
