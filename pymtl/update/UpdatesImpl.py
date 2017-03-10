#=========================================================================
# UpdatesImpl.py
#=========================================================================
# At the bottom level, we only have update blocks and explicit constraints
# between two update blocks/one update block and the read/write of a
# python variable.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# call A before B.
# We collect two types of constraints at this level:
# * Implicit constraint: upA reads s.x while upB writes s.x ==> upB < upA
# * Explicit constraint: s.add_constraints( upA < upB )
# Explicit constraints will override implicit constraints.

from collections import defaultdict, deque

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
