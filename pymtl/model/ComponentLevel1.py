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

  # Global block index for update blocks that were stripped of their
  # instance variable closures.
  global_blk_idx = 0

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

  def strip_closure( s, blk ):
    """ Given an update block function, create a new function with s
    variable stripped and instead fed through as a parameter. """

    fun_body = p.sub( "", blk.src )
    ComponentLevel1.global_blk_idx += 1

    new_blk_name = "{}__{}".format( blk.__name__, ComponentLevel1.global_blk_idx )

    def reindent( code, indent ):
      """ Given python code of arbitrary indentation, re-indents the
      string with indent number of spaces. """

      # First find the first non-space line of code.
      for l in code.splitlines():
        if l.isspace() or l == "":
          continue
        current_indent = len(l) - len( l.lstrip( " " ) )
        break

      return "\n".join( ( ( " " * indent ) + l[ current_indent : ]
                          for l in code.splitlines() ) )

    # If the update block has closures other than s, we still need to
    # provide those closed over variables.
    closure_cpy = "\n"
    for i, var in enumerate( blk.__code__.co_freevars ):
      if var == "s":
        continue

      # Pick a name to store the closed over value that we attach to s.
      closure_field_name = "___clsr_{}__{}".format( blk.__name__, var )
      closure_cpy += "    {} = s.{}\n".format( var, closure_field_name )
      s.__dict__[ closure_field_name ] = blk.__closure__[i].cell_contents


    src = """def get_blk_without_closure():
  def {0}( s ):
    {2}
    {1}
  return {0}

new_blk = get_blk_without_closure()""".format(
                              new_blk_name, reindent( fun_body, 4 ), closure_cpy )

    var = locals()
    # Grab the function's view of globals.
    var.update( blk.__globals__ )
    exec py.code.Source( src ).compile() in var

    blk.blk_without_closure = new_blk
    return new_blk

  def record_update_block( s, blk ):
    """ Registers the update block with the framework. """

    s._cache_func_meta( blk )

    cls = type(s)

    # Attach "_blks" attribute to the class that the block is defined. We
    # will use this later to find similar update blocks that execute the
    # same code but have a different instance variable.
    if not hasattr( cls, "_blks" ):
      cls._blks = {}
      cls._blks_without_closure = {}

    name = blk.__name__

    if name not in cls._blks:
      cls._blks[ name ] = []

    assert blk not in cls._blks

    # The blk_without_closure is the version of this update block that
    # strips away the closures and feeds the instance variable s through a
    # parameter. This is None initially, but strip_closure can be called
    # to initialize it.
    blk.blk_without_closure = None

    cls._blks[ name ].append( blk )
    blk.hostobj = s


  def update( s, blk ):
    name = blk.__name__
    if name in s._name_upblk:
      raise UpblkFuncSameNameError( name )

    s.record_update_block( blk )
    s._name_upblk[ name ] = s._id_upblk[ id(blk) ] = blk
    return blk

  def compile_update_block( s, src ): # FIXME
    var = locals()
    var.update( globals() ) # the src may have Bits
    exec py.code.Source( src ).compile() in var
    s.record_update_block( blk )
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
