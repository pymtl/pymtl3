#=========================================================================
# DynamicSchedulePass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from BasePass     import BasePass, PassMetadata
from collections  import deque
from graphviz     import Digraph
from errors import PassOrderError
from pymtl.dsl.errors import UpblkCyclicError

class DynamicSchedulePass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    top._sched = PassMetadata()

    top._sched.schedule = self.schedule( top )
    top.tick = self.generate_tick( top )

  def schedule( self, top ):

    # Construct the graph

    V  = top.get_all_update_blocks() | top._dag.genblks
    E  = top._dag.all_constraints
    G   = { v: [] for v in V }
    G_T = { v: [] for v in V } # transpose graph

    for (u, v) in E: # u -> v
      G  [u].append( v )
      G_T[v].append( u )

    #---------------------------------------------------------------------
    # Run Kosaraju's algorithm to shrink all strongly connected components
    # (SCCs) into super nodes
    #---------------------------------------------------------------------

    def get_reverse_post_order( G ):
      visited = set()
      post_order = []

      def dfs_post_order( u ):
        visited.add( u )
        for v in G[u]:
          if v not in visited:
            dfs_post_order( v )
        post_order.append( u )

      import random
      vertices = G.keys()
      random.shuffle(vertices)
      for u in vertices:
        if u not in visited:
          dfs_post_order( u )
      return post_order[::-1]

    # First dfs on G to generate reverse post-order (RPO)

    RPO = get_reverse_post_order( G )

    # Second bfs on G_T to generate SCCs

    SCCs  = []
    v_SCC = {}
    visited = set()

    for u in RPO:
      if u not in visited:
        visited.add( u )
        scc = set()
        SCCs.append( scc )
        Q = deque( [u] )
        scc.add( u )
        while Q:
          u = Q.popleft()
          v_SCC[u] = len(SCCs) - 1
          for v in G_T[u]:
            if v not in visited:
              visited.add( v )
              Q.append( v )
              scc.add( v )

    # Construct a new graph of SCCs

    G_new = { i: set() for i in range(len(SCCs)) }
    InD   = { i: 0     for i in range(len(SCCs)) }

    for (u, v) in E: # u -> v
      if v_SCC[u] != v_SCC[v]:
        InD[ v_SCC[v] ] += 1
        G_new[ v_SCC[u] ].add( v_SCC[v] )

    # Perform topological sort on SCCs

    schedule = []

    Q = deque( [ i for i in range(len(SCCs)) if not InD[i] ] )

    while Q:
      u = Q.pop()
      schedule.append( SCCs[u] )
      for v in G_new[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    return schedule

  def generate_tick( self, top ):
    schedule        = top._sched.schedule
    all_constraints = top._dag.all_constraints

    blocks_funcs = []

    for scc in schedule:
      if len(scc) == 1:
        block_funcs = list(scc)[0]
      else:
        for (u, v) in all_constraints:
          if u in scc and v in scc:
            print u, v
        # generate a loop for scc
        print top._dag.constraint_objects
