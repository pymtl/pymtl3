#=========================================================================
# UpdateOnly.py
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
from errors          import UpblkSameNameError
from pymtl.datatypes import *

import inspect2, re, ast, py
p = re.compile('( *(@|def))')

class UpdateOnly( NamedObject ):

  def __new__( cls, *args, **kwargs ):
    inst = NamedObject.__new__( cls, *args, **kwargs )

    inst._name_upblk = {}
    inst._id_upblk   = {}
    inst._U_U_constraints = set() # contains ( id(func), id(func) )s

    return inst

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      assert isinstance( x0, U ) and isinstance( x1, U ), "Only accept up1<up2"
      s._U_U_constraints.add( (id(x0.func), id(x1.func)) )

  def update( s, blk ):
    blk_name = blk.__name__
    if blk_name in s._name_upblk:
      raise UpblkSameNameError( blk.__name__ )

    # Cache the source and ast of update blocks in the type object

    cls = type(s)
    if not hasattr( cls, "_blkname_src" ):
      assert not hasattr( cls, "_blkname_ast" )
      cls._blkname_src = {}
      cls._blkname_ast = {}

    if blk_name not in cls._blkname_src:
      src = p.sub( r'\2', inspect2.getsource(blk) )
      cls._blkname_src[ blk_name ] = src
      cls._blkname_ast[ blk_name ] = ast.parse( src )

    blk.hostobj = s
    blk.ast     = cls._blkname_ast[ blk_name ]
    s._name_upblk[ blk_name ] = s._id_upblk[ id(blk) ] = blk
    return blk

  def compile_update_block( s, src ): # FIXME
    var = locals()
    var.update( globals() ) # the src may have Bits
    exec py.code.Source( src ).compile() in var
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  # Elaboration steps. Child classes should override it.

  def elaborate( s ):
    s._tag_name_collect()
    s._declare_vars()
    s._elaborate()
    s._process_constraints()

  # Elaboration template. Child classes shouldn't override this.

  def _elaborate( s ):
    for obj in s._all_objects:
      s._elaborate_vars( obj )
      s._collect_vars( obj )

  # These functions should be overriden, but remember to call super method
  # whenever necessary

  def _process_constraints( s ):
    s._constraints = s._expl_constraints.copy()

  def _declare_vars( s ):
    s._blkid_upblk = {}
    s._expl_constraints = set()

  def _elaborate_vars( s, m ):
    pass

  def _collect_vars( s, m ):
    if isinstance( m, UpdateOnly ):
      s._blkid_upblk.update( m._id_upblk )
      s._expl_constraints.update( m._U_U_constraints )
