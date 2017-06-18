#-------------------------------------------------------------------------
# ScheduleUpblkPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from collections  import deque, defaultdict
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.components.errors import UpblkCyclicError

class ScheduleUpblkPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def apply( self, m ):
    if not hasattr( m, "_blkid_upblk" ):
      raise PassOrderError( "_blkid_upblk" )
    if not hasattr( m, "_constraints" ):
      raise PassOrderError( "_constraints" )

    self.schedule( m )

  #-------------------------------------------------------------------------
  # schedule
  #-------------------------------------------------------------------------
  # Based on all constraints on the update block list, calculate a feasible
  # static schedule for update blocks. This schedule funtion returns two
  # schedules: serial_schedule and batch_schedule. The former is just ready
  # to go, while the latter one is more for dataflow analysis purpose.

  def schedule( self, m ):

    # Construct the graph

    vs  = m._blkid_upblk.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(m._constraints): # u -> v, always
      InD[v] += 1
      OuD[u] += 1
      es [u].append( v )

    # Perform topological sort for a serial schedule.

    Q = deque()
    for v in vs:
      if not InD[v]:
        Q.append( v )
      # if not InD[v] and not OuD[v]:
        # print "Warning: update block \"{}\" has no constraint".format( m._blkid_upblk[v].__name__ )

    serial_schedule = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later
      u = Q.pop()
      serial_schedule.append( m._blkid_upblk[u] )
      for v in es[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    if len(serial_schedule) != len(vs):
      raise UpblkCyclicError( """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """)

    # Extract batches of frontiers which gives better idea for dataflow

    InD = { v:0 for v in vs }

    for u in es.values():
      for v in u:
        InD[v] += 1

    Q = deque()
    for v in vs:
      if not InD[v]:
        Q.append( v )

    batch_schedule = []

    while Q:
      Q2 = deque()
      batch_schedule.append( [ m._blkid_upblk[v] for v in Q ] )
      for u in Q:
        for v in es[u]:
          InD[v] -= 1
          if not InD[v]:
            Q2.append( v )
      Q = Q2

    m._serial_schedule = serial_schedule
    m._batch_schedule  = batch_schedule
