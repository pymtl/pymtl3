#=========================================================================
# UpdateVar.py
#=========================================================================

from UpdateOnly      import UpdateOnly
from ConstraintTypes import U, RD, WR, ValueConstraint
from collections     import defaultdict
from errors import InvalidConstraintError
import AstHelper

import inspect2, re, ast
p = re.compile('( *(@|def))')

class UpdateVar( UpdateOnly ):

  def __new__( cls, *args, **kwargs ):
    inst = super(UpdateVar, cls).__new__( cls, *args, **kwargs )

    inst._update_on_edge   = set()
    # constraint[id(var)] = (sign, id(func))
    inst._RD_U_constraints = defaultdict(list)
    inst._WR_U_constraints = defaultdict(list)
    inst._name_func = {}
    inst._id_func   = {}

    return inst

  # @s.func is for those functions

  def func( s, func ):
    func_name = func.__name__

    if func_name in s._name_func:
      raise FuncSameNameError( func.__name__ )

    # Cache the source and ast of functions in the type object

    cls = type(s)

    if not hasattr( cls, "_funcname_src" ):
      assert not hasattr( cls, "_funcname_ast" )
      assert not hasattr( cls, "_funcname_rd" )
      assert not hasattr( cls, "_funcname_wr" )
      cls._funcname_src = {}
      cls._funcname_ast = {}
      cls._funcname_rd = {}
      cls._funcname_wr = {}
      cls._funcname_fc = {}

    if func_name not in cls._funcname_src:
      src = p.sub( r'\2', inspect2.getsource(func) )
      cls._funcname_src[ func_name ] = src
      cls._funcname_ast[ func_name ] = ast.parse( src )

    func.ast = cls._funcname_ast[ func_name ]
    func.hostobj = s
    s._name_func[ func_name ] = s._id_func[ id(func) ] = func

    if func_name not in cls._funcname_rd:
      cls._funcname_rd[ func_name ] = rd = []
      cls._funcname_wr[ func_name ] = wr = []
      cls._funcname_fc[ func_name ] = fc = []
      AstHelper.extract_read_write( func, rd, wr )
      AstHelper.extract_func_calls( func, fc )

    return func

  # Override
  def update( s, blk ):
    blk_name = blk.__name__
    super( UpdateVar, s ).update( blk )

    # Cache reads/write NAMEs within update blocks in the type object

    cls = type(s)

    if not hasattr( cls, "_blkname_rd" ):
      assert not hasattr( cls, "_blkname_wr" )
      cls._blkname_rd = {}
      cls._blkname_wr = {}
      cls._blkname_fc = {}

    if blk_name not in cls._blkname_rd:
      cls._blkname_rd[ blk_name ] = rd = []
      cls._blkname_wr[ blk_name ] = wr = []
      cls._blkname_fc[ blk_name ] = fc = []
      AstHelper.extract_read_write( blk, rd, wr )
      AstHelper.extract_func_calls( blk, fc )

    # blk.rd/wr = [ (name, astnode) ]
    blk.rd = cls._blkname_rd[ blk_name ]
    blk.wr = cls._blkname_wr[ blk_name ]
    blk.fc = cls._blkname_fc[ blk_name ]
    return blk

  def update_on_edge( s, blk ):
    s._update_on_edge.add( id(blk) )
    return s.update( blk )

  # Override
  def add_constraints( s, *args ):

    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U, same
        s._U_U_constraints.add( (id(x0.func), id(x1.func)) )

      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        raise InvalidConstraintError

      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U is 1, RD(x) > U is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0 # Make sure x0 is RD/WR(...) and x1 is U(...)

        if isinstance( x0, RD ):
          s._RD_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )
        else:
          s._WR_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )
