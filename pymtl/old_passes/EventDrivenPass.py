#-------------------------------------------------------------------------
# EventDrivenPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from ScheduleUpblkPass import ScheduleUpblkPass
from SignalCleanupPass import SignalCleanupPass
from pymtl.model.Connectable import _overlap
import ast, py
from collections import deque, defaultdict

class EventDrivenPass( BasePass ):

  def apply( self, m, mode='unroll' ):
    if not isinstance( m, RTLComponent ):
      raise ModelTypeError( "RTLComponent" )

    m.elaborate()
    ScheduleUpblkPass().apply( m )
    self.wrap_change_detect( m )
    SignalCleanupPass().apply( m )

  @staticmethod
  def wrap_change_detect( m ):

    # Basically reuse the code for implicit constraints to construct
    # sensitivity dict

    m._blk_sensitivity_blks = { x : defaultdict(set)
                                for x in m._all_id_upblk.values() }

    # Enumerate the variables. For each x, attach all blks that read x
    # to the list triggered by x

    read_upblks  = m._all_read_upblks
    write_upblks = m._all_write_upblks

    for rd_id, rd_blks in read_upblks.iteritems():
      obj     = m._id_obj[ rd_id ]
      writers = []

      # Check parents. Cover 1) and 2)
      x = obj
      while x:
        if id(x) in write_upblks:
          writers.append( id(x) )
        x = x._nested

      # Check the sibling slices. Cover 3)
      if obj._slice:
        for x in obj._nested._slices.values():
          if _overlap( x._slice, obj._slice ) and id(x) in write_upblks:
            writers.append( id(x) )

      # Add all constraints
      for writer in writers:
        for wr_blk in write_upblks[ writer ]:
          for rd_blk in rd_blks:
            if wr_blk != rd_blk:
              if rd_blk not in m._all_update_on_edge:
                # writer <--> rd_blk
                m._blk_sensitivity_blks[ m._all_id_upblk[wr_blk] ] \
                                       [ m._id_obj[writer] ].add( m._all_id_upblk[rd_blk] )

    for wr_id, wr_blks in write_upblks.iteritems():
      obj     = m._id_obj[ wr_id ]
      readers = []

      x = obj
      while x:
        if id(x) in read_upblks:
          readers.append( id(x) )
        x = x._nested

      # Add all constraints
      for wr_blk in wr_blks:
        for reader in readers:
          for rd_blk in read_upblks[ reader ]:
            if wr_blk != rd_blk:
              if rd_blk not in m._all_update_on_edge:
                m._blk_sensitivity_blks[ m._all_id_upblk[wr_blk] ] \
                                       [ m._id_obj[wr_id] ].add( m._all_id_upblk[rd_blk] )

    # for wr_blk, sens in m._blk_sensitivity_blks.iteritems():
      # print 
      # print "== blk {} ==".format( wr_blk.__name__ )
      # for var, rd_blks in sens.iteritems():
        # print " - ",var,":",[ x.__name__ for x in rd_blks ]

    # Here we denote blk as the original block or whatever stores original
    # update blocks, and w_blk as the wrapped version of them

    # First get all update blocks affected by input port
    default_blks = set( m._batch_schedule[0] )

    for read in read_upblks:
      x = m._id_obj[read]
      if isinstance( x, InVPort ):
        if hasattr(x, "_host"):
          if x._host == m:
            # TODO find host for ports only appears in upblks
            for blkid in read_upblks[read]:
              default_blks.add( m._all_id_upblk[ blkid ] )
        else:
          host = x
          while not isinstance( host, RTLComponent ):
            host = host._parent # go to the component
          x._host = host
          if x._host == m:
            for blkid in read_upblks[read]:
              print m._all_id_upblk[ blkid ]
              default_blks.add( m._all_id_upblk[ blkid ] )

    # Fix the order of update blocks

    all_upblks = sorted( list(m._all_id_upblk.values()), key=lambda x: x.__name__ )
    upblk_id   = { all_upblks[i]: i for i in xrange(len(all_upblks)) }
    m._default_blks = []

    # Discretize all signals

    signals = sorted([ (x, y) for _, z in m._blk_sensitivity_blks.iteritems()
                       for x, y in z.iteritems() ], key=lambda x: repr(x[0]) )

    signal_id = { signals[i][0]: i for i in xrange(len(signals)) }

    m._sensitivity  = [ [] for i in signals ]
    m._event_set    = set()

    # Generate tick

    def tick():
      for x in m._default_blks:
        x()
      while m._event_set:
        blk = m._event_set.pop()
        blk()

    m.tick = tick

    w_all_blks = []

    from copy import copy
    for blk in all_upblks:
      sense = m._blk_sensitivity_blks[ blk ]
      tot = 0
      for sig, blks in sense.iteritems():
        tot += len(blks)

      if tot == 0: # Nothing to trigger
        w_all_blks.append( blk )
      else:
        # will trigger other blks
        copy_srcs  = []
        check_srcs = []
        idx = 0
        for sig, blks in sense.iteritems():
          if len(blks) > 0:
            copy_srcs.append( "___t_m_p_{} = copy({})".format( idx, sig ) )
            check_srcs.append( "if {} != ___t_m_p_{}:".format( sig, idx ) )
            check_srcs.append( "  event_set.update( m._sensitivity[ {} ] )"
                                    .format( signal_id[ sig ] ) )
            idx += 1 

        src = """
        def gen_wrapped_blk( s, blk ):
          sensitivity = s._sensitivity
          event_set = s._event_set

          def w_{0}():
            {1}
            blk()
            {2}

          return w_{0}
        """.format( blk.__name__, "\n            ".join( copy_srcs ),
                    "\n            ".join( check_srcs ) )
        exec py.code.Source( src ).compile() in locals()
        w_blk = gen_wrapped_blk( m, blk )
        w_all_blks.append( w_blk )

    for x in default_blks:
      m._default_blks.append( w_all_blks[ upblk_id[x] ] )

    for i in xrange(len(signals)):
      for x in signals[i][1]:
        m._sensitivity[i].append( w_all_blks[ upblk_id[x] ] )
