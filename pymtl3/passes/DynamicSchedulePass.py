#=========================================================================
# DynamicSchedulePass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from __future__ import absolute_import, division, print_function

import os
from collections import deque

import py

from .BasePass import BasePass, PassMetadata
from .errors import PassOrderError
from .SimpleSchedulePass import dump_dag


class DynamicSchedulePass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    top._sched = PassMetadata()

    top._sched.schedule = self.schedule( top )

  def schedule( self, top ):

    # Construct the graph

    V  = top.get_all_update_blocks() | top._dag.genblks
    E  = top._dag.all_constraints
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

    #---------------------------------------------------------------------
    # Now we generate super blocks for each SCC and produce final schedule
    #---------------------------------------------------------------------

    constraint_objs = top._dag.constraint_objs

    schedule = []

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
          in_degree_ranking = sorted( [ (InD[v], v) for v in InD ] )
          Q.append( in_degree_ranking[0][1] )

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

        # generate a loop for scc
        # Shunning: we just simply loop over the whole SCC block
        # TODO performance optimizations using Mamba techniques within a SCC block

        def gen_wrapped_SCCblk( s, scc, src ):
          from pymtl3.dsl.errors import UpblkCyclicError

          # print src
          exec(py.code.Source( src ).compile(), locals())

          return generated_block

        template = """
          from copy import deepcopy
          def wrapped_SCC_{0}():
            num_iters = 0
            while True:
              num_iters += 1
              {1}
              for blk in scc: # TODO Mamba
                blk()
              if {2}:
                break
              if num_iters > 100:
                raise UpblkCyclicError("Combinational loop detected at runtime in {{{3}}}!")
            # print "SCC block{0} is executed", num_iters, "times"
          generated_block = wrapped_SCC_{0}
        """

        copy_srcs  = []
        check_srcs = []

        for j, var in enumerate(variables):
          copy_srcs .append( "_____tmp_{} = deepcopy({})".format( j, var ) )
          check_srcs.append( "{} == _____tmp_{}".format( var, j ) )

        scc_block_src = template.format( scc_id,
                                         "; ".join( copy_srcs ),
                                         " and ".join( check_srcs ),
                                         ", ".join( [ x.__name__ for x in scc] ) )
        schedule.append( gen_wrapped_SCCblk( top, tmp_schedule, scc_block_src ) )

    return schedule
