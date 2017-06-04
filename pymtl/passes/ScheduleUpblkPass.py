#-------------------------------------------------------------------------
# ScheduleUpblkPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass
from collections  import deque, defaultdict
from graphviz     import Digraph

class ScheduleUpblkPass( BasePass ):
  def __init__( self, dump = False ):
    self.dump = dump

  def execute( self, m ):
    assert hasattr( m, "_blkid_upblk" ), "Please apply other passes to generate model._blkid_upblk"
    assert hasattr( m, "_constraints" ), "Please apply other passes to generate model._constraints"

    serial, batch = self.schedule( m._blkid_upblk, m._constraints )
    m._serial_schedule = serial
    m._batch_schedule  = batch

    if self.dump:
      # self.print_upblk_dag( m._blkid_upblk, m._constraints )
      self.print_schedule( serial, batch )

    return m

  #-------------------------------------------------------------------------
  # schedule
  #-------------------------------------------------------------------------
  # Based on all constraints on the update block list, calculate a feasible
  # static schedule for update blocks. This schedule funtion returns two
  # schedules: serial_schedule and batch_schedule. The former is just ready
  # to go, while the latter one is more for dataflow analysis purpose.

  @staticmethod
  def schedule( upblk_dict, constraints ):

    # Construct the graph

    vs  = upblk_dict.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(constraints): # u -> v, always
      InD[v] += 1
      OuD[u] += 1
      es [u].append( v )

    # Perform topological sort for a serial schedule.

    Q = deque()
    for v in vs:
      if not InD[v]:
        Q.append( v )
      # if not InD[v] and not OuD[v]:
        # print "Warning: update block \"{}\" has no constraint".format( upblk_dict[v].__name__ )

    serial_schedule = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later
      u = Q.pop()
      serial_schedule.append( upblk_dict[u] )
      for v in es[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    if len(serial_schedule) != len(vs):
      assert False, """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """

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
      batch_schedule.append( [ upblk_dict[v] for v in Q ] )
      for u in Q:
        for v in es[u]:
          InD[v] -= 1
          if not InD[v]:
            Q2.append( v )
      Q = Q2

    return serial_schedule, batch_schedule

  @staticmethod
  def print_upblk_dag( upblk_dict, constraints ):
    dot = Digraph()
    dot.graph_attr["rank"] = "source"
    dot.graph_attr["ratio"] = "fill"
    dot.graph_attr["margin"] = "0.1"

    for x in upblk_dict.values():
      dot.node( x.__name__+"@"+repr(x.hostobj) )

    for (x, y) in constraints:
      upx, upy = upblk_dict[x], upblk_dict[y]
      dot.edge( upx.__name__+"@"+repr(upx.hostobj),
                upy.__name__+"@"+repr(upy.hostobj) )
    dot.render( "/tmp/upblk-dag.gv", view=True )

  @staticmethod
  def print_schedule( serial, batch ):
    print
    print "+-------------------------------------------------------------"
    print "+ Update block schedule"
    print "+-------------------------------------------------------------"
    print
    print "* Serial:"
    for (i, blk) in enumerate( serial ):
      print " ", i, blk.__name__
    print
    print "* Batch:"
    for x in batch:
      print " ", [ y.__name__ for y in x ]
