#=========================================================================
# UpdateWithVar.py
#=========================================================================

from UpdateOnly      import UpdateOnly
from ConstraintTypes import U, RD, WR
import AstHelper

class UpdateWithVar( UpdateOnly ):

  def __new__( cls, *args, **kwargs ):
    inst = super(UpdateWithVar, cls).__new__( cls, *args, **kwargs )

    inst._update_on_edge   = set()
    # constraint[id(var)] = (sign, id(func))
    inst._RD_U_constraints = defaultdict(list)
    inst._WR_U_constraints = defaultdict(list)

    return inst

  # Override
  def update( s, blk ):
    blk_name = blk.__name__
    super( UpdateWithVar, s ).update( blk )

    # Cache reads/write NAMEs within update blocks in the type object

    cls = type(s)

    if not hasattr( cls, "_blkname_rd" ):
      assert not hasattr( cls, "_blkname_wr" )
      cls._blkname_rd = {}
      cls._blkname_wr = {}

    if blk_name not in cls._blkname_rd:
      cls._blkname_rd[ blk_name ] = rd = []
      cls._blkname_wr[ blk_name ] = wr = []
      AstHelper.extract_read_write( blk.ast, blk, rd, wr )

    blk.rd = cls._blkname_rd[ blk_name ]
    blk.wr = cls._blkname_wr[ blk_name ]
    return blk

  def update_on_edge( s, blk ):
    s._update_on_edge.add( id(blk) )
    return s.update( blk )

  # Override
  def add_constraints( s, *args ):

    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U, same
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )

      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        assert False, "Constraints between two variables are not allowed!"

      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U(x) is 1, RD(x) > U(x) is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0 # Make sure x0 is RD/WR(...) and x1 is U(...)

        if isinstance( x0, RD ):
          s._RD_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )
        else:
          s._WR_U_constraints[ id(x0.var) ].append( (sign, id(x1.func) ) )
