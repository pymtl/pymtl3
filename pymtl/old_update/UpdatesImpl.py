#=========================================================================
# UpdatesImpl.py
#=========================================================================
# We collect two types of implicit constraints at this level:
# * upA reads Wire s.x while upB writes Wire s.x ==> upB < upA
# * upA is marked as update_on_edge ==> for all upblks upX that write/read
#   variables in upA, upA < upX

from UpdatesExpl import verbose
from UpdatesConnection import UpdatesConnection
from Connectable import overlap

class UpdatesImpl( UpdatesConnection ):

  def __new__( cls, *args, **kwargs ):
    inst = super(UpdatesImpl, cls).__new__( cls, *args, **kwargs )
    inst._update_on_edge = set()
    return inst

  def update_on_edge( s, blk ):
    s.update( blk )
    s._update_on_edge.add( id(blk) )
    return blk

  # Override
  def _collect_child_vars( s, child ):
    super( UpdatesImpl, s )._collect_child_vars( child )
    if isinstance( child, UpdatesImpl ):
      s._update_on_edge.update( child._update_on_edge )

  # Override
  def _synthesize_constraints( s ):

    # Explicit constraints are collected in super classes

    super( UpdatesImpl, s )._synthesize_constraints()

    #---------------------------------------------------------------------
    # Implicit constraint
    #---------------------------------------------------------------------
    # Synthesize total constraints between two upblks that read/write to
    # the "same variable" (we also handle the read/write of a recursively
    # nested field/slice)

    read_blks  = s._read_blks
    write_blks = s._write_blks
    id_obj     = s._id_obj

    impl_c = set()

    # Collect all objs that write the variable whose id is "read"
    # 1) RD A.b.b     - WR A.b.b, A.b, A
    # 2) RD A.b[1:10] - WR A.b[1:10], A,b, A
    # 3) RD A.b[1:10] - WR A.b[0:5], A.b[6], A.b[8:11]

    for read, rd_blks in read_blks.iteritems():
      obj     = id_obj[ read ]
      writers = []

      # Check parents. Cover 1) and 2)
      x = obj
      while x:
        xid = id(x)
        if xid in write_blks:
          writers.append( xid )
        x = x._parent

      # Check the sibling slices. Cover 3)
      if obj._slice:
        for x in obj._parent._slices.values():
          if overlap( x._slice, obj._slice ) and id(x) in write_blks:
            writers.append( id(x) )

      # Add all constraints
      for writer in writers:
        for wr in write_blks[ writer ]:
          for rd in rd_blks:
            if wr != rd:
              if rd in s._update_on_edge:
                impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
              else:
                impl_c.add( (wr, rd) ) # wr < rd by default

    # Collect all objs that read the variable whose id is "write"
    # 1) WR A.b.b.b, A.b.b, A.b, A (detect 2-writer conflict)
    # 2) WR A.b.b.b   - RD A.b.b, A.b, A
    # 3) WR A.b[1:10] - RD A.b[1:10], A,b, A
    # 4) WR A.b[1:10], A.b[0:5], A.b[6] (detect 2-writer conflict)
    # "WR A.b[1:10] - RD A.b[0:5], A.b[6], A.b[8:11]" has been discovered

    for write, wr_blks in write_blks.iteritems():
      obj     = id_obj[ write ]
      readers = []

      # Check parents. Cover 1), 2) and 3)
      x = obj
      while x:
        xid = id(x)
        if xid != write:
          assert xid not in write_blks, "Two-writer conflict in nested data struct/slice. \n - %s (in %s)\n - %s (in %s)" % \
                                        ( x.full_name(), s._blkid_upblk[write_blks[xid][0]].__name__, obj.full_name(), s._blkid_upblk[write_blks[id(obj)][0]].__name__ )
        if xid in read_blks:
          readers.append( xid )
        x = x._parent

      # Check the sibling slices. Cover 4)
      if obj._slice:
        for x in obj._parent._slices.values():
          # Recognize overlapped slices
          if id(x) != id(obj) and overlap( x._slice, obj._slice ):
            assert id(x) not in write_blks, "Two-writer conflict in nested data struct/slice. \n - %s (in %s)\n - %s (in %s)" % \
                                        ( x.full_name(), s._blkid_upblk[write_blks[id(x)][0]].__name__, obj.full_name(), s._blkid_upblk[write_blks[id(obj)][0]].__name__ )

      # Add all constraints
      for wr in wr_blks:
        for reader in readers:
          rd_blks = read_blks[ reader ]
          for rd in rd_blks:
            if wr != rd:
              if rd in s._update_on_edge:
                impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
              else:
                impl_c.add( (wr, rd) ) # wr < rd by default

    if verbose:
      for (x, y) in impl_c:
        print s._blkid_upblk[x].__name__.center(25)," (<) ", s._blkid_upblk[y].__name__.center(25)

      for (x, y) in s._expl_constraints:
        print s._blkid_upblk[x].__name__.center(25),"  <  ", s._blkid_upblk[y].__name__.center(25)

    for (x, y) in impl_c:
      if (y, x) not in s._expl_constraints: # no conflicting expl
        s._total_constraints.add( (x, y) )

      if (x, y) in s._expl_constraints or (y, x) in s._expl_constraints:
        print "implicit constraint is overriden -- ",s._blkid_upblk[x].__name__, " (<) ", \
               s._blkid_upblk[y].__name__

    s._total_constraints = list(s._total_constraints)
