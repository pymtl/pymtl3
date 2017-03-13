#=========================================================================
# UpdatesImpl.py
#=========================================================================
# We collect two types of implicit constraints at this level:
# * upA reads s.x while upB writes s.x ==> upB < upA
# * upA is marked as update_on_edge ==> first batch of upblks called


from UpdatesExpl import UpdatesExpl, verbose

class UpdatesImpl( UpdatesExpl ):

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

    #---------------------------------------------------------------------
    # Implicit constraint
    #---------------------------------------------------------------------
    # Synthesize total constraints between two upblks that read/write to
    # the same variable.

    read_blks  = s._read_blks
    write_blks = s._write_blks

    impl_c = set()

    for read, rd_blks in read_blks.iteritems():
      wr_blks = write_blks[ read ] # writes to the same variable
      for wr in wr_blks:
        for rd in rd_blks:
          if wr != rd:
            if rd in s._update_on_edge:
              impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
            else:
              impl_c.add( (wr, rd) ) # wr < rd by default

    for write, wr_blks in write_blks.iteritems():
      rd_blks = read_blks[ write ]
      for wr in wr_blks:
        for rd in rd_blks:
          if wr != rd:
            if rd in s._update_on_edge:
              impl_c.add( (rd, wr) ) # rd < wr if blk rd is on edge
            else:
              impl_c.add( (wr, rd) ) # wr < rd by default

    s._total_constraints = s._expl_constraints.copy()

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
