#=========================================================================
# UpdatesExpl.py
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

class UpdateOnly( NamedObject ):

  def __new__( cls, *args, **kwargs ):
    inst = NamedObject.__new__( cls, *args, **kwargs )

    # These will be collected recursively
    inst._name_upblk      = {}
    inst._blkid_upblk     = {}
    inst._U_U_constraints = set() # contains ( id(func), id(func) )s
    return inst

  def update( s, blk ):
    blk_name = blk.__name__
    assert blk_name not in s._name_upblk, """
      Cannot declare two update blocks with the same name {}
    """.format( blk_name )

    s._name_upblk[ blk_name ] = s._blkid_upblk[ id(blk) ] = blk
    return blk

  def add_update_block( s, src ):
    exec py.code.Source( src ).compile() in locals()

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      assert isinstance( x0, U ) and isinstance( x1, U ), "Only accept up1<up2"
      s._U_U_constraints.add( (id(x0.func), id(x1.func)) )
