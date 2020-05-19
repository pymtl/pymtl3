#=========================================================================
# DynamicSchedulePass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

import os
from collections import defaultdict, deque
from copy import deepcopy

import py

from pymtl3.datatypes import Bits, is_bitstruct_class
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.extra.pypy import custom_exec
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError

from .SimpleSchedulePass import SimpleSchedulePass, dump_dag
from .SimpleTickPass import SimpleTickPass


class DynamicSchedulePass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    if hasattr( top, "_sched" ):
      raise Exception("Some schedule pass has already been applied!")

    top._sched = PassMetadata()

    self.schedule_intra_cycle( top )

    # Reuse simple's ff and flip schedule
    simple = SimpleSchedulePass()
    simple.schedule_ff( top )
    simple.schedule_posedge_flip( top )

  def schedule_intra_cycle( self, top ):

    # Construct the intra-cycle graph based on normal update blocks

    V   = top._dag.final_upblks - top.get_all_update_ff()

    G   = { v: [] for v in V }
    G_T = { v: [] for v in V } # transpose graph

    E = set()
    for (u, v) in top._dag.all_constraints: # u -> v
      if u in V and v in V:
        G  [u].append( v )
        G_T[v].append( u )
        E.add( (u, v) )

    if 'MAMBA_DAG' in os.environ:
      dump_dag( top, V, E )

    # Compute SCC using Kosaraju's algorithm

    SCCs, G_new = kosaraju_scc( G, G_T )

    # Perform topological sort on SCCs

    InD = { i: 0 for i in range(len(SCCs)) }
    for u, vs in G_new.items():
      for v in vs:
        InD[ v ] += 1

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
    onces = top.get_all_update_once()

    # Put the graph schedule to _sched
    top._sched.update_schedule = schedule = []

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

        # check update_once first
        for x in scc:
          if x in onces:
            raise UpblkCyclicError("update_once blocks are not allowed to appear in a cycle. \n - " + \
                            "\n - ".join( [
                              f"{y.__name__} ({'@update_once' if y in onces else '@update'} " \
                              f"in 'top.{repr(top.get_update_block_host_component(y))[2:]}')"
                              for y in scc] ))

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
          raise UpblkCyclicError("There is a cyclic dependency without involving variables."
                          "Probably a loop that involves blocks that should be update_once:\n{}"\
                          .format(", ".join( [ x.__name__ for x in scc] )))

        # generate a loop for scc
        # Shunning: we just simply loop over the whole SCC block
        # TODO performance optimizations using Mamba techniques within a SCC block

        def gen_wrapped_SCCblk( s, scc, src ):

          # TODO mamba?
          scc_tick_func = SimpleTickPass.gen_tick_function( scc )
          _globals = { 's': s, 'scc_tick_func': scc_tick_func, 'deepcopy': deepcopy,
                       'UpblkCyclicError': UpblkCyclicError }
          _locals  = {}

          custom_exec(py.code.Source( src ).compile(), _globals, _locals)
          return _locals[ 'generated_block' ]

        template = """
def wrapped_SCC_{0}():
  N = 0
  while True:
    N += 1
    if N > 100:
      raise UpblkCyclicError("Combinational loop detected at runtime in {{{3}}} after 100 iters!")
    {1}
    scc_tick_func()
    {2}
    # print( "SCC block{0} is executed", num_iters, "times" )
    break
generated_block = wrapped_SCC_{0}
          """

        copy_srcs  = []
        check_srcs = []
        # print_srcs = []

        # clean up non-top variables if top is there. remove slices

        final_variables = set()

        for x in sorted( variables, key=repr ):
          w = x.get_top_level_signal()
          if w is x:
            final_variables.add( x )
            continue

          # w is not x
          if issubclass( w._dsl.Type, Bits ):
            if w not in final_variables:
              final_variables.add( w )
          elif is_bitstruct_class( w._dsl.Type ):
            if w not in final_variables:
              final_variables.add( x )
          else:
            final_variables.add( x )

        # group them by host component so that we create less bytecode

        final_var_host = defaultdict(list)
        for x in final_variables:
          final_var_host[ x.get_host_component() ].append( x )

        # create a block of copy/check code for each host component. Need
        # to allocate global var_id across different host components.

        var_id = 0
        for host, var_list in final_var_host.items():

          copy_srcs .append( f"host={host!r}" )
          check_srcs.append( f"host={host!r}" )

          sub_check_srcs = []

          hostlen = len(repr(host))
          for var in var_list:
            var_id += 1
            subname = repr(var)[hostlen+1:]
            if issubclass( var._dsl.Type, Bits ):     copy_srcs.append( f"t{var_id}=host.{subname}.clone()" )
            elif is_bitstruct_class( var._dsl.Type ): copy_srcs.append( f"t{var_id}=host.{subname}.clone()" )
            else:                                     copy_srcs.append( f"t{var_id}=deepcopy(host.{subname})" )

            sub_check_srcs.append( f"host.{subname} != t{var_id}" )

          check_srcs.append( f"if { ' or '.join(sub_check_srcs)}: continue" )

        scc_block_src = template.format( scc_id, "; ".join( copy_srcs ), "\n    ".join( check_srcs ),
                                         ", ".join( [ x.__name__ for x in scc] ) )

        # print(scc_block_src)
        schedule.append( gen_wrapped_SCCblk( top, tmp_schedule, scc_block_src ) )

def kosaraju_scc( G, G_T ):

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
    # random.shuffle(vertices)
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

    for u, vs in G.items():
      for v in vs: # u -> v
        scc_u, scc_v = v_SCC[u], v_SCC[v]
        if scc_u != scc_v and scc_v not in G_new[ scc_u ]:
          G_new[ scc_u ].add( scc_v )

    return SCCs, G_new
