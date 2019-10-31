#=========================================================================
# DynamicSchedulePass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

import os
import random
from collections import deque

import py

from .BasePass import BasePass, PassMetadata
from .errors import PassOrderError
from .SimpleSchedulePass import dump_dag, make_double_buffer_func
from .SimpleTickPass import SimpleTickPass


class DynamicSchedulePass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    top._sched = PassMetadata()

    top._sched.schedule = self.schedule( top )

  def schedule( self, top ):

    # Construct the graph

    V   = top._dag.final_upblks - top.get_all_update_ff()
    E   = top._dag.all_constraints
    G   = { v: [] for v in V }
    G_T = { v: [] for v in V } # transpose graph

    if 'MAMBA_DAG' in os.environ:
      dump_dag( top, V, E )

    for (u, v) in E: # u -> v
      G  [u].append( v )
      G_T[v].append( u )

    #---------------------------------------------------------------------
    # Run Kosaraju's algorithm to shrink all strongly connected components
    # (SCCs) into super nodes
    #---------------------------------------------------------------------

    # First dfs on G to generate reverse post-order (RPO)
    # Shunning: we emulate the system stack to implement non-recursive
    # post-order DFS algorithm. At the beginning, I implemented a more
    # succinct recursive DFS but it turned out that a 1500-depth chain in
    # the graph will reach the CPython max recursion depth.
    # https://docs.python.org/3/library/sys.html#sys.getrecursionlimit

    PO = []

    vertices = list(G.keys())
    random.shuffle(vertices)
    visited = set()

    # The commented algorithm loyally emulates the system stack by storing
    # the loop index in each stack element and push only one new element
    # to stack in every iteration. This is basically what recursive dfs
    # does.
    #
    # for u in vertices:
    #   if u not in visited:
    #     stack = [ (u, False) ]
    #     while stack:
    #       u, idx = stack.pop()
    #       visited.add( u )
    #       if idx == len(G[u]):
    #         PO.append( u )
    #       else:
    #         while idx < len(G[u]) and G[u][-idx] in visited:
    #           idx += 1
    #         if idx < len(G[u]):
    #           stack.append( (u, idx) )
    #           stack.append( (G[u][-idx], 0) )
    #         else:
    #           PO.append( u )

    # The following algorithm push all adjacent elements to the stack at
    # once and later check visited set to avoid redundant visit (instead
    # of checking visited set when pushing element to the stack). I added
    # a second_visit flag to add the node to post-order.

    for u in vertices:
      stack = [ (u, False) ]
      while stack:
        u, second_visit = stack.pop()

        if second_visit:
          PO.append( u )
        elif u not in visited:
          visited.add( u )
          stack.append( (u, True) )
          for v in reversed(G[u]):
            stack.append( (v, False) )

    RPO = PO[::-1]

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
      scc_u, scc_v = v_SCC[u], v_SCC[v]
      if scc_u != scc_v and scc_v not in G_new[ scc_u ]:
        InD[ scc_v ] += 1
        G_new[ scc_u ].add( scc_v )

    # Perform topological sort on SCCs

    scc_pred = {}
    scc_schedule = []

    Q = deque( [ i for i in range(len(SCCs)) if not InD[i] ] )
    for x in Q:
      scc_pred[ x ] = None

    while Q:
      u = Q.pop()
      scc_schedule.append( u )
      for v in G_new[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )
          scc_pred[ v ] = u

    assert len(scc_schedule) == len(SCCs)

    #---------------------------------------------------------------------
    # Now we generate super blocks for each SCC and produce final schedule
    #---------------------------------------------------------------------

    constraint_objs = top._dag.constraint_objs

    # From now on, we put the schedule in the order of
    # [ flip, normal upblks, update_ffs ]

    schedule = [ make_double_buffer_func( top ) ]

    scc_id = 0
    for i in scc_schedule:
      scc = SCCs[i]
      if len(scc) == 1:
        schedule.append( list(scc)[0] )
      else:

        # For each non-trivial SCC, we need to figure out a intra-SCC
        # linear schedule that minimizes the time to re-execute this SCC
        # due to value changes. A bad schedule may inefficiently execute
        # the SCC for many times, each of which changes a few signals.
        # The current algorithm iteratively finds the "entry block" of
        # the SCC and expand its adjancent blocks. The implementation is
        # to first find the actual entry point, and then BFS to expand the
        # footprint until all nodes are visited.

        tmp_schedule = []
        Q = deque()

        if scc_pred[i] is None:
          # We start bfs from the block that has the least number of input
          # edges in the SCC
          InD = { v: 0 for v in scc }
          for (u, v) in E: # u -> v
            if u in scc and v in scc:
              InD[ v ] += 1
          Q.append( max(InD, key=InD.get) )

        else:
          # We start bfs with the blocks that are successors of the
          # predecessor scc in the previous SCC-level topological sort.
          pred = set( SCCs[ scc_pred[i] ] )
          # Sort by names for a fixed outcome
          for x in sorted( scc, key = lambda x: x.__name__ ):
            for v in G_T[x]: # find reversed edges point back to pred SCC
              if v in pred:
                Q.append( x )

        # Perform bfs to find a heuristic schedule
        visited = set(Q)
        while Q:
          u = Q.popleft()
          tmp_schedule.append( u )
          for v in G[u]:
            if v in scc and v not in visited:
              Q.append( v )
              visited.add( v )

        scc_id += 1
        variables = set()
        for (u, v) in E:
          # Collect all variables that triggers other blocks in the SCC
          if u in scc and v in scc:
            variables.update( constraint_objs[ (u, v) ] )

        if len(variables) == 0:
          raise Exception("There is a cyclic dependency without involving variables."
                          "Probably a loop that involves update_once:\n{}".format(", ".join( [ x.__name__ for x in scc] )))

        # generate a loop for scc
        # Shunning: we just simply loop over the whole SCC block
        # TODO performance optimizations using Mamba techniques within a SCC block

        def gen_wrapped_SCCblk( s, scc, src ):
          from pymtl3.dsl.errors import UpblkCyclicError

          # TODO mamba?
          scc_tick_func = SimpleTickPass.gen_tick_function( scc )
          namespace = {}
          namespace.update( locals() )

          exec(py.code.Source( src ).compile(), namespace)
          return namespace['generated_block']

        template = """
          from copy import deepcopy
          def wrapped_SCC_{0}():
            N = 0
            while True:
              N += 1
              if N > 100: raise UpblkCyclicError("Combinational loop detected at runtime in {{{3}}} after 100 iters!")
              {1}
              scc_tick_func()
              if {2}:
                break
            # print "SCC block{0} is executed", num_iters, "times"
          generated_block = wrapped_SCC_{0}
        """

        copy_srcs  = []
        check_srcs = []
        # print_srcs = []

        for j, var in enumerate(variables):
          copy_srcs .append( "t{} = deepcopy({})".format( j, var ) )
          check_srcs.append( "{} == t{}".format( var, j ) )
          # print_srcs.append( "print '{}', {}, _____tmp_{}".format( var, var, j ) )

        scc_block_src = template.format( scc_id,
                                         "; ".join( copy_srcs ),
                                         " and ".join( check_srcs ),
                                         ", ".join( [ x.__name__ for x in scc] ) )
                                         # "; ".join( print_srcs ) )
        schedule.append( gen_wrapped_SCCblk( top, tmp_schedule, scc_block_src ) )

    schedule.extend( list(top._dsl.all_update_ff) )

    return schedule
