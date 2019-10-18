"""
-------------------------------------------------------------------------
TraceBreakingSchedTickPas.py
-------------------------------------------------------------------------
Generate the schedule and tick with trace breaking + heuristic toposort.

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
import py
from graphviz import Digraph

from pymtl3.dsl import *
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError
from pymtl3.passes.SimpleSchedulePass import check_schedule

from .HeuristicTopoPass import CountBranches


class TraceBreakingSchedTickPass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    top._sched = PassMetadata()

    self.meta_schedule( top )
    self.trace_breaking_tick( top )

  def meta_schedule( self, top ):

    # Construct the graph

    V   = top._dag.final_upblks
    E   = top._dag.all_constraints
    Es  = { v: [] for v in V }
    InD = { v: 0  for v in V }

    for (u, v) in E: # u -> v
      InD[v] += 1
      Es [u].append( v )

    # Extract branchiness

    # Initialize all generated net block to 0 branchiness
    branchiness = { x: 0 for x in top._dag.genblks }

    visitor = CountBranches()
    for blk in top.get_all_update_blocks():
      hostobj = top.get_update_block_host_component( blk )
      branchiness[ blk ] = visitor.enter( hostobj.get_update_block_info( blk )[-1] )

    # Shunning: now we make the scheduling aware of meta blocks
    # Basically we enhance the topological sort to choose
    # branchy/unbranchy block based on the progress of the current meta
    # block. If there is no branch at all along the meta block, I let it
    # grow as long as possible. If we have to append one branchy update
    # block, we then append a couple of branchy blocks till the
    # branchiness bound is reached, after which we break the trace.
    #
    # TODO now I'm using binary-search. Ideally a double-ended
    # priority queue or a balanced binary search tree (AVL/Treap/RB) can
    # reduce it to O(nlogn). I didn't find any efficient python impl.

    def insert_sortedlist( arr, priority, item ):
      left, right = 0, len(arr)
      while left < right-1:
        mid = (left + right) >> 1
        if priority <= arr[mid][0]:
          right = mid
        else:
          left = mid
      arr.insert( right, (priority, item) )

    Q = []
    for v in V:
      if not InD[v]:
        br = branchiness[ v ]
        insert_sortedlist( Q, br, v )

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 8

    # Block factor is the bound of the number of branchy blocks in a
    # meta block.
    branchy_block_factor = 4

    schedule = []

    metas = []
    current_meta = []
    current_branchiness = current_blk_count = 0

    while Q:
      # If currently there is no branchiness, append less branchy block
      if current_branchiness == 0:
        (br, u) = Q.pop(0)

        # Update the current
        current_blk_count += 1
        current_branchiness += br
        current_meta.append( u )

        if current_branchiness >= branchiness_factor:
          metas.append( current_meta )
          current_branchiness = current_blk_count = 0
          current_meta = []

      # We already append a branchy block
      else:
        # Find the most branchy block
        (br, u) = Q.pop()

        # If no branchy block available, directly start a new metablock

        if not br:
          metas.append( current_meta )
          current_branchiness = current_blk_count = 0
          current_meta = [ u ]

        # Limit the number of branchiness and number of branchy blocks

        elif current_branchiness + br <= branchiness_factor:
          current_meta.append( u )
          current_branchiness += br
          current_blk_count += 1

          if current_blk_count >= branchy_block_factor:
            metas.append( current_meta )
            current_branchiness = current_blk_count = 0
            current_meta = []

        else:
          current_meta.append( u )
          metas.append( current_meta )
          current_branchiness = current_blk_count = 0
          current_meta = []

      schedule.append( u )
      for v in Es[u]:
        InD[v] -= 1
        if not InD[v]:
          insert_sortedlist( Q, branchiness[ v ], v )

    # Append the last meta block
    if current_meta:
      metas.append( current_meta )

    print("num_metablks:", len(metas))

    for meta in metas:
      print("---------------")
      for blk in meta:
        print(" - {}: {}".format( blk.__name__, branchiness[ blk ] ))

    top._sched.meta_schedule = metas
    self.branchiness = branchiness

    check_schedule( top, schedule, V, E, InD )

  def trace_breaking_tick( self, top ):
    metas = top._sched.meta_schedule

    # We will use pypyjit.dont_trace_here to disable tracing across
    # intermediate update blocks.
    gen_tick_src =  "try:\n"
    gen_tick_src += "  from pypyjit import dont_trace_here\n"
    gen_tick_src += "except ImportError:\n"
    gen_tick_src += "  pass\n"

    # The "comment" that will be used for update calls.
    schedule_names = {}

    for i in range( len(metas) ):
      meta = metas[i]
      for j in range( len(meta) ):
        blk = meta[j]
        schedule_names[ (i, j) ] = "[br: {}] {}" \
          .format( self.branchiness[ blk ], blk.__name__ )

        # Copy the scheduled functions to update_blkX__Y
        gen_tick_src += "update_blk{0}__{1} = metas[{0}][{1}];".format( i, j )

    for i in range( len(metas) ):
      meta_blk = metas[i]

      gen_tick_src += "\n\ndef meta_blk{}():\n  ".format(i)

      gen_tick_src += "\n  ".join( [ "update_blk{}__{}() # {}" \
                                    .format( i, j, schedule_names[(i, j)] )
                                    for j in range( len(meta_blk) )] )

      if i < len(metas)-1:
        gen_tick_src += "\ntry:\n"
        gen_tick_src += "  dont_trace_here(0, False, meta_blk{}.__code__)\n".format( i )
        gen_tick_src += "except NameError:\n"
        gen_tick_src += "  pass\n"

    gen_tick_src += "\ndef tick_top():\n  "
    gen_tick_src += "; ".join( [ "meta_blk{}()".format(i) for i in range(len(metas)) ] )

    local = locals()
    exec(py.code.Source( gen_tick_src ).compile(), local )

    #  print gen_tick_src
    top.tick = local["tick_top"]
