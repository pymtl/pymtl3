#-------------------------------------------------------------------------
# SimpleSchedTickPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass
from collections  import deque
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.model.errors import UpblkCyclicError

class SimpleSchedTickPass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    schedule = self.schedule( top )

    def tick_normal():
      for blk in schedule:
        blk()

    top.tick = tick_normal

  def schedule( self, top ):

    # Construct the graph

    V   = top.get_all_update_blocks() | top.genblks
    E   = top.all_constraints
    Es  = { v: [] for v in V }
    InD = { v: 0  for v in V }

    for (u, v) in E: # u -> v
      InD[v] += 1
      Es [u].append( v )

    # Perform topological sort for a serial schedule.

    schedule = []

    Q = deque( [ v for v in V if not InD[v] ] )

    while Q:
      u = Q.pop()
      schedule.append( u )
      for v in Es[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    if len(schedule) != len(V):
      from graphviz import Digraph
      dot = Digraph()
      dot.graph_attr["rank"] = "same"
      dot.graph_attr["ratio"] = "compress"
      dot.graph_attr["margin"] = "0.1"

      leftovers = set( [ v for v in V if InD[v] ] )
      for x in leftovers:
        dot.node( x.__name__+"\\n@"+repr(x.hostobj), shape="box")

      for (x, y) in E:
        if x in leftovers and y in leftovers:
          dot.edge( x.__name__+"\\n@"+repr(x.hostobj),
                    y.__name__+"\\n@"+repr(y.hostobj) )
      dot.render( "/tmp/upblk-dag.gv", view=True )

      raise UpblkCyclicError( """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """)

    assert schedule, "No update block found in the model"

    return schedule
