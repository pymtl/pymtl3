#=========================================================================
# Mamba2020Pass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Feb 14, 2020

import os
import random
from collections import deque

import py

from pymtl3.dsl import MethodPort
from pymtl3.datatypes import Bits, is_bitstruct_class
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError
from pymtl3.utils import custom_exec

from .HeuristicTopoPass import CountBranchesLoops
from .UnrollTickPass import UnrollTickPass
from ..sim.DynamicSchedulePass import kosaraju_scc
from ..sim.SimpleSchedulePass import SimpleSchedulePass, dump_dag
from ..sim.SimpleTickPass import SimpleTickPass

_DEBUG = True
# _DEBUG = False

class Mamba2020Pass( BasePass ):

  def __init__( self ):
    self.meta_block_id = 0

  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    if hasattr( top, "_sched" ):
      raise Exception("Some schedule pass has already been applied!")

    top._sched = PassMetadata()

    # Extract branchiness first
    # Initialize all generated net block to 0 branchiness

    self.branchiness = { x: 0 for x in top._dag.genblks }
    self.only_loop_at_top = { x: False for x in top._dag.genblks }
    v = CountBranchesLoops()

    for blk in top.get_all_update_blocks():
      hostobj = top.get_update_block_host_component( blk )
      self.branchiness[ blk ], self.only_loop_at_top[ blk ] = v.enter( hostobj.get_update_block_info( blk )[-1] )

    # count=0
    # for i, x in enumerate( sorted(list(self.branchiness.items()), key=lambda x:x[1]) ):
      # print(i, x)
      # if x[1]>0:
        # count+=1
    # print(len(self.branchiness), count)

    self.schedule_ff( top )

    # Reuse simple's flip schedule
    simple = SimpleSchedulePass()
    simple.schedule_posedge_flip( top )

    self.schedule_intra_cycle( top )


    self.assemble_tick( top )

  #-----------------------------------------------------------------------
  # compile_meta_block
  #-----------------------------------------------------------------------
  # Util function to compile and trace-break a list of update blocks

  def compile_meta_block( self, blocks ):

    meta_id = self.meta_block_id
    self.meta_block_id += 1

    # Create custom global dict for all blocks inside the meta block
    _globals = { f"blk{i}": b for i, b in enumerate( blocks ) }

    gen_src = f"def meta_block{meta_id}():\n  "
    gen_src += "\n  ".join( [ f"blk{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" \
                              for i, b in enumerate(blocks) ] )
    # use custom_exec to compile the meta block

    _locals = {}
    custom_exec( py.code.Source( gen_src ).compile(), _globals, _locals )
    ret = _locals[ f'meta_block{meta_id}' ]
    if _DEBUG: print(gen_src)

    # We will use pypyjit.dont_trace_here to compile standalone traces for
    # each meta block
    try:
      from pypyjit import dont_trace_here
      dont_trace_here( 0, False, ret.__code__ )
    except:
      pass

    return ret

  #-----------------------------------------------------------------------
  # schedule_ff
  #-----------------------------------------------------------------------
  # Schedule all update_ff blocks to meta blocks
  # This one is actually easier because we can order them arbitrarily

  def schedule_ff( self, top ):

    top._sched.schedule_ff = schedule = []
    if not top.get_all_update_ff():
      return

    # tuples in ffs: ( awesomeloop, branchiness, blk )

    ffs = [ (self.only_loop_at_top[x], self.branchiness[x], x) for x in top.get_all_update_ff() ]
    ffs = sorted( ffs, key=lambda x:x[:2] )

    # Divide all blks into meta blocks

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 30

    # Block factor is the bound of the number of branchy blocks in a
    # meta block.
    branchy_block_factor = 30

    cur_meta, cur_br, cur_count = [], 0, 0

    for i, (loop, br, blk) in enumerate( ffs ):
      if loop: # this means the remaining blocks are all loops
        if cur_meta:
          schedule.append( self.compile_meta_block( cur_meta ) )
        for j in range(i, len(ffs)):
          schedule.append( ffs[j][2] )
        break

      if br == 0:
        cur_meta.append( blk )

      else: # this means the remaining blocks are all branchy
        cur_meta.append( blk )
        cur_br += br
        cur_count += 1

        if cur_br >= branchiness_factor or cur_count >= branchy_block_factor:
          schedule.append( self.compile_meta_block( cur_meta ) )
          cur_br = cur_count = 0
          cur_meta = []

    if cur_meta:
      schedule.append( self.compile_meta_block( cur_meta ) )

  #-----------------------------------------------------------------------
  # schedule_intra_cycle
  #-----------------------------------------------------------------------
  # This is the real entree

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

    # Now we generate super blocks for each SCC and produce final schedule

    constraint_objs = top._dag.constraint_objs

    # Perform topological sort on SCCs

    InD = { i: 0 for i in range(len(SCCs)) }
    nontrivial_sccs   = set()
    trivial_loop_sccs = set()

    for u, vs in G_new.items():
      if len(SCCs[u]) > 1:
        nontrivial_sccs.add( u )
      elif self.only_loop_at_top[ list(SCCs[u])[0] ]:
        trivial_loop_sccs.add( u )

      for v in vs:
        InD[ v ] += 1

    # Shunning: reuse this from TraceBreakingPass. Not the most
    # efficient one

    def insert_sortedlist( arr, priority, item ):
      left, right = 0, len(arr)
      while left < right-1:
        mid = (left + right) >> 1
        if priority <= arr[mid][0]:
          right = mid
        else:
          left = mid
      arr.insert( left, (priority, item) )

    scc_pred = {}

    Q_trivial = []
    Q_nontrivial = deque()
    for v in range(len(SCCs)):
      if not InD[v]:
        scc_pred[v] = None
        if v in nontrivial_sccs or v in trivial_loop_sccs:
          Q_nontrivial.append( v )
        else:
          insert_sortedlist( Q_trivial, self.branchiness[list(SCCs[v])[0]], v )

    # Put the graph schedule to _sched
    top._sched.update_schedule = schedule = []

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 20

    # Block factor is the bound of the number of branchy blocks in a
    # meta block.
    branchy_block_factor = 10
    cur_meta = []
    cur_br = cur_count = 0

    scc_id = 0

    def expand_node( u ):
      for v in G_new[u]:
        InD[v] -= 1
        if not InD[v]:
          scc_pred[ v ] = u
          if v in nontrivial_sccs or v in trivial_loop_sccs:
            Q_nontrivial.append( v )
          else:
            insert_sortedlist( Q_trivial, self.branchiness[list(SCCs[v])[0]], v )

    # Run topological sort

    while Q_trivial or Q_nontrivial:
      # Is it possible that Q_nontrivial extend itself?
      # Is it possbile that cur_meta got cut in the middle???

      if Q_trivial:
        if cur_br == 0:
          (br, u) = Q_trivial.pop(0)
          scc = list(SCCs[u])[0]

          cur_meta.append( scc )
          cur_br += br
          if br > 0:
            cur_count += 1

          if cur_br >= branchiness_factor:
            schedule.append( self.compile_meta_block( cur_meta ) )
            cur_br = cur_count = 0
            cur_meta.clear()

        else:
          (br, u) = Q_trivial.pop()

          scc = list(SCCs[u]) [0]
          # If no branchy block available, directly start a new metablock
          if br == 0:
            schedule.append( self.compile_meta_block( cur_meta ) )
            cur_br = cur_count = 0
            cur_meta.clear()

            cur_meta.append( scc )

          # Limit the number of branchiness and number of branchy blocks
          else:
            cur_meta.append( scc )
            cur_br += br
            cur_count += 1

            if cur_br + br >= branchiness_factor or cur_count + 1 >= branchy_block_factor:
              schedule.append( self.compile_meta_block( cur_meta ) )
              cur_br = cur_count = 0
              cur_meta.clear()

        expand_node( u )

      else:
        if cur_meta:
          schedule.append( self.compile_meta_block( cur_meta ) )
          cur_br = cur_count = 0
          cur_meta.clear()

        while Q_nontrivial:
          i = Q_nontrivial.popleft()
          scc = SCCs[i]

          # expand first
          expand_node( i )

          # Generate a func for SCC

          # Trivial -- continue
          if len(scc) == 1:
            schedule.append( list(scc)[0] )
            if _DEBUG: print(list(scc)[0])
            continue

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

          template = """
            from copy import deepcopy
            def wrapped_SCC_{0}():
              N = 0
              while True:
                N += 1
                if N > 100:
                  raise Exception("Combinational loop detected at runtime in {{{3}}} after 100 iters!")
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
            if issubclass( var._dsl.Type, Bits ):     copy_srcs.append( f"t{j}={var}.clone()" )
            elif is_bitstruct_class( var._dsl.Type ): copy_srcs.append( f"t{j}={var}.clone()" )
            else:                                     copy_srcs.append( f"t{j}=deepcopy({var})" )
            check_srcs.append( f"{var} == t{j}" )

          scc_block_src = template.format( scc_id, "; ".join( copy_srcs ), " and ".join( check_srcs ),
                                           ", ".join( [ x.__name__ for x in scc] ) )

          # Divide all blks into meta blocks
          # Branchiness factor is the bound of branchiness in a meta block.
          branchiness_factor = 10
          branchy_block_factor = 8

          cur_meta, cur_br, cur_count = [], 0, 0

          metas = []
          for i, blk in enumerate( tmp_schedule ):
            br = self.branchiness[blk]
            if cur_br == 0:
              cur_meta.append( blk )
              cur_br += br
              cur_count += 1
              if cur_br >= branchiness_factor or cur_count >= branchy_block_factor:
                metas.append( self.compile_meta_block( cur_meta ) )
                cur_br = cur_count = 0
                cur_meta = []
            elif cur_br > 0 and br == 0:
              # If no branchy block available, directly start a new metablock
              schedule.append( self.compile_meta_block( cur_meta ) )
              cur_br = cur_count = 0
              cur_meta.clear()
              cur_meta.append( blk )

          if cur_meta:
            metas.append( self.compile_meta_block( cur_meta ) )

          scc_tick_func = UnrollTickPass.gen_tick_function( metas )

          _globals = { 's': top, 'scc_tick_func': scc_tick_func }
          _locals  = {}
          if _DEBUG: print(scc_block_src)

          custom_exec(py.code.Source( scc_block_src ).compile(), _globals, _locals)

          schedule.append( _locals[ 'generated_block' ] )

    if cur_meta:
      schedule.append( self.compile_meta_block( cur_meta ) )

  def assemble_tick( self, top ):

    final_schedule = []

    # call ff blocks first
    final_schedule.extend( top._sched.schedule_ff )

    # append tracing related work

    if hasattr( top, "_tracing" ):
      if hasattr( top._tracing, "vcd_func" ):
        final_schedule.append( top._tracing.vcd_func )
      if hasattr( top._tracing, "collect_text_sigs" ):
        final_schedule.append( top._tracing.collect_text_sigs )

    # posedge flip
    final_schedule.extend( top._sched.schedule_posedge_flip )

    # advance cycle after posedge
    def generate_advance_sim_cycle( top ):
      def advance_sim_cycle():
        top.simulated_cycles += 1
      return advance_sim_cycle
    final_schedule.append( generate_advance_sim_cycle(top) )

    # clear cl method flag
    if hasattr( top, "_tracing" ):
      if hasattr( top._tracing, "clear_cl_trace" ):
        final_schedule.append( top._tracing.clear_cl_trace )

    # execute all update blocks
    final_schedule.extend( top._sched.update_schedule )

    # Generate tick
    top.tick = UnrollTickPass.gen_tick_function( final_schedule )
    # reset sim_cycles
    top.simulated_cycles = 0

    # FIXME update_once?
    # check if the design has method_port
    method_ports = top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) )

    if len(method_ports) == 0:
      # Pure RTL design, add eval_combinational
      top.eval_combinational = SimpleTickPass.gen_tick_function( top._sched.update_schedule )
    else:
      tmp = list(method_ports)[0]
      def eval_combinational():
        raise NotImplementedError(f"top is not a pure RTL design. {'top'+repr(tmp)[1:]} is a method port.")
      top.eval_combinational = eval_combinational

    # print("="*50)
    # for x in final_schedule:
      # print(x)
