#-------------------------------------------------------------------------
# ScheduleUpblkPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
from collections  import deque, defaultdict
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.model.errors import UpblkCyclicError

class ScheduleUpblkPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def apply( self, m ):
    if not hasattr( m, "_all_constraints" ):
      raise PassOrderError( "_all_constraints" )

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

    vs  = m._all_id_upblk.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(m._all_constraints): # u -> v, always
      InD[v] += 1
      es [u].append( v )

    # Perform topological sort for a serial schedule.

    Q      = deque( [ v for v in vs if not InD[v] ] )
    serial = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later
      u = Q.pop()
      serial.append( m._all_id_upblk[u] )
      for v in es[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    if len(serial) != len(vs):
      raise UpblkCyclicError( """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """)

    # Extract batches of frontiers which gives better idea for dataflow

    InD = { v:0 for v in vs }

    for u in es.values():
      for v in u:
        InD[v] += 1

    Q     = deque( [ v for v in vs if not InD[v] ] )
    batch = []

    while Q:
      Q2 = deque()
      batch.append( [ m._all_id_upblk[v] for v in Q ] )
      for u in Q:
        for v in es[u]:
          InD[v] -= 1
          if not InD[v]:
            Q2.append( v )
      Q = Q2

    m._serial_schedule = serial
    m._batch_schedule  = batch
