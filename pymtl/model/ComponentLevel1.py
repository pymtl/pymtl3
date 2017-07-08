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
p = re.compile('( *(@|def))')

class ComponentLevel1( NamedObject ):

  def __new__( cls, *args, **kwargs ):
    """ Convention: variables local to the object is created in __new__ """

    inst = NamedObject.__new__( cls, *args, **kwargs )

    inst._name_upblk = {}
    inst._id_upblk   = {}
    inst._U_U_constraints = set() # contains ( id(func), id(func) )s

    return inst

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      assert isinstance( x0, U ) and isinstance( x1, U ), "Only accept up1<up2"
      s._U_U_constraints.add( (id(x0.func), id(x1.func)) )

  def _cache_func_meta( s, func ):
    """ Convention: the source of a function/update block across different
    instances should be the same. You can construct different functions
    based on the condition, but please use different names. This not only
    keeps the caching valid, but also make the code more readable.

    According to the convention, we can cache the information of a
    function in the *class object* to avoid redundant parsing. """

    cls  = type(s)
    if not hasattr( cls, "_name_src" ):
      cls._name_src = {}
      cls._name_ast = {}

    name = func.__name__
    if name not in cls._name_src:
      cls._name_src[ name ] = src = p.sub( r'\2', inspect2.getsource(func) )
      cls._name_ast[ name ] = ast.parse( src )

    func.src = cls._name_src[ name ]
    func.ast = cls._name_ast[ name ]

  def update( s, blk ):
    name = blk.__name__
    if name in s._name_upblk:
      raise UpblkFuncSameNameError( name )

    s._cache_func_meta( blk )

    blk.hostobj = s
    s._name_upblk[ name ] = s._id_upblk[ id(blk) ] = blk
    return blk

  def compile_update_block( s, src ): # FIXME
    var = locals()
    var.update( globals() ) # the src may have Bits
    exec py.code.Source( src ).compile() in var
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  # These functions are called during elaboration and should be overriden,
  # but remember to call super method whenever necessary.

  def elaborate( s ):
    """ Elaboration steps. Child classes should override and rewrite it. """

    s._declare_vars()
    s._tag_name_collect()

    for obj in s._id_obj.values():
      assert isinstance( obj, ComponentLevel1 ) # just component
      s._collect_vars( obj )

    s._process_constraints()

  def _declare_vars( s ):
    """ Convention: the component on which we call elaborate declare
    variables in _declare_vars; it shouldn't have them before elaboration.

    Convention: the variables that hold all metadata of descendants
    should have _all prefix."""

    s._all_id_upblk = {}
    s._all_expl_constraints = set()

  def _collect_vars( s, m ):
    """ Called on individual objects during elaboration.
    The general format resembles "s._all_X.update/append( s._X ). """

    if isinstance( m, ComponentLevel1 ):
      s._all_id_upblk.update( m._id_upblk )
      s._all_expl_constraints.update( m._U_U_constraints )

  def _process_constraints( s ):
    s._all_constraints = s._all_expl_constraints.copy()
