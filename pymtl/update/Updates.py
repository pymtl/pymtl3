#=========================================================================
# Updates.py
#=========================================================================
# We add implicit constraints at this level to have full-blown
# UpdatesComponent. We collect two types of implicit constraints:
# * upA reads Wire s.x while upB writes Wire s.x ==> upB < upA
# * upA is marked as update_on_edge ==> for all upblks upX that write/read
#   variables in upA, upA < upX

from UpdatesExpl import verbose
from UpdatesConnection import UpdatesConnection

class Updates( UpdatesConnection ):

  def __new__( cls, *args, **kwargs ):
    inst = super(Updates, cls).__new__( cls, *args, **kwargs )
    inst._update_on_edge = set()
    return inst

  def update_on_edge( s, blk ):
    s.update( blk )
    s._update_on_edge.add( id(blk) )
    return blk

  # Override
  def _collect_child_vars( s, child ):
    super( Updates, s )._collect_child_vars( child )
    if isinstance( child, Updates ):
      s._update_on_edge.update( child._update_on_edge )

  # Override
  def _synthesize_constraints( s ):

    # Explicit constraints are collected in super classes

    super( Updates, s )._synthesize_constraints()

    #---------------------------------------------------------------------
    # Implicit constraint
    #---------------------------------------------------------------------
    # Synthesize total constraints between two upblks that read/write to
    # the same variable.

    read_blks  = s._read_blks
    write_blks = s._write_blks
    id_obj     = s._id_obj

    impl_c = set()

    # We also handle the read/write of a recursively nested field

    for read, rd_blks in read_blks.iteritems():
      obj = id_obj[ read ]

      # RD A.b.b.b:
      #  - WR A.b.b, A.b, A (recognize implicit constraint)

      while obj:
        # Be careful! defaultdict will create a KV pair during []
        wr_blks = write_blks[ id(obj) ] if id(obj) in write_blks else []

        for wr in wr_blks:
          for rd in rd_blks:
            if wr != rd:
              if rd in s._update_on_edge:
                impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
              else:
                impl_c.add( (wr, rd) ) # wr < rd by default
        obj = obj._father

    for write, wr_blks in write_blks.iteritems():
      obj = id_obj[ write ]

      # WR A.b.b.b:
      # - RD A.b.b, A.b, A (recognize implicit constraint)
      # - WR A.b.b, A.b, A (detect 2-writer conflict)

      while obj:
        if id(obj) != write:
          assert id(obj) not in write_blks, "Two-writer conflict in nested data struct! \n - %s\n - %s" % \
                                            ( id_obj[ write ].full_name(), obj.full_name() )
        rd_blks = read_blks[ id(obj) ] if id(obj) in read_blks else []

        for wr in wr_blks:
          for rd in rd_blks:
            if wr != rd:
              if rd in s._update_on_edge:
                impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
              else:
                impl_c.add( (wr, rd) ) # wr < rd by default
        obj = obj._father

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
