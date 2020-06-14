#=========================================================================
# Mamba2020Pass.py
#=========================================================================
# This pass implements trace breaking techniques and supports non-DAG, so
# we don't need the old TraceBreaking pass which only supports DAG
# anymore.
#
# Author : Shunning Jiang
# Date   : Feb 14, 2020

import os
from collections import defaultdict, deque

import py

from pymtl3.datatypes import Bits, is_bitstruct_class
from pymtl3.dsl import MethodPort
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.extra.pypy import custom_exec
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError

from ..sim.DynamicSchedulePass import kosaraju_scc
from ..sim.SimpleSchedulePass import SimpleSchedulePass, dump_dag
from .HeuristicTopoPass import CountBranchesLoops
from .UnrollSimPass import UnrollSimPass

# _DEBUG = True
_DEBUG = False

class Mamba2020Pass( UnrollSimPass ):

  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    if hasattr( top, "_sched" ):
      raise Exception("Some schedule pass has already been applied!")

    top._sched = PassMetadata()

    # Extract branchiness first
    # Initialize all generated net block to 0 branchiness

    self.meta_block_id = 0
    self.branchiness = { x: 0 for x in top._dag.genblks }
    self.only_loop_at_top = { x: False for x in top._dag.genblks }
    v = CountBranchesLoops()

    # Shunning: since each loop turns into call_assembler_r, a pure-loop
    # update block is basically 0 branchiness and can be inserted anywhere.
    # At the beginning I tried not to put those blocks into any metablock
    # to avoid double call_assembler_r but it just turned out that there
    # is no difference of where you put the call_assembler_r.. Plus,
    # treating loop blocks as normal update block can activate subsequent
    # schedulable 0-branchiness block.

    for blk in top.get_all_update_blocks():
      hostobj = top.get_update_block_host_component( blk )
      if blk in top._dag.blk_greenlet_mapping:
        gblk = top._dag.blk_greenlet_mapping[ blk ]
        self.branchiness[ gblk ], self.only_loop_at_top[ gblk ] = 0, 0
      else:
        self.branchiness[ blk ], self.only_loop_at_top[ blk ] = v.enter( hostobj.get_update_block_info( blk )[-1] )

    self.schedule_ff( top )

    # Reuse simple's flip schedule
    simple = SimpleSchedulePass()
    simple.schedule_posedge_flip( top )

    self.schedule_intra_cycle( top )

    top._sim = PassMetadata()
    self.create_print_line_trace( top )
    self.create_sim_cycle_count( top )
    self.create_lock_unlock_simulation( top )
    top.lock_in_simulation()

    self.create_sim_eval_comb( top )
    self.create_sim_tick( top )
    self.create_sim_reset( top )

  #-----------------------------------------------------------------------
  # compile_meta_block
  #-----------------------------------------------------------------------
  # Util function to compile and trace-break a list of update blocks

  def compile_meta_block( self, blocks ):

    meta_id = self.meta_block_id
    self.meta_block_id += 1

    # Create custom global dict for all blocks inside the meta block
    _globals = { f"blk{i}": b for i, b in enumerate( blocks ) }

    blk_srcs = []
    for i, b in enumerate(blocks):
      # This is a normal update block
      if b in self.branchiness:
        blk_srcs.append( f"blk{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
      # This is an SCC block which has zero BR and is a loop
      else:
        blk_srcs.append( f"blk{i}() # {b.__name__}" )

    gen_src = f"def meta_block{meta_id}():\n  "
    gen_src += "\n  ".join( blk_srcs )

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

    # tuples in ffs: ( branchiness, blk )

    ffs = []
    for x in top.get_all_update_ff():
      # Here we treat loop-only upblk as 0 branchiness
      ffs.append( (0 if self.only_loop_at_top[x] else self.branchiness[x], x) )
    ffs = sorted( ffs, key=lambda x:x[0] )

    # Divide all blks into meta blocks

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 20

    # Block factor is the bound of the number of branchy blocks in a
    # meta block.
    branchy_block_factor = 6

    cur_meta, cur_br, cur_count = [], 0, 0

    for i, (br, blk) in enumerate( ffs ):
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

    onces = top.get_all_update_once()
    # This function compiles a SCC block
    scc_id = 0 # global id across all sccs
    def compile_scc( i ):
      nonlocal scc_id

      scc = SCCs[i]

      if len(scc) == 1:
        return list(scc)[0]

      for x in scc:
        if x in onces:
          raise UpblkCyclicError("update_once blocks are not allowed to appear in a cycle. \n - " + \
                          "\n - ".join( [
                            f"{y.__name__} ({'@update_once' if y in onces else '@update'} " \
                            f"in 'top.{repr(top.get_update_block_host_component(y))[2:]}')"
                            for y in scc] ))

      scc_id += 1
      if _DEBUG: print( f"{'='*100}\n SCC{scc_id}\n{'='*100}" )

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

      template = """
from copy import deepcopy
def wrapped_SCC_{0}():
  N = 0
  while True:
    N += 1
    if N > 100:
      raise UpblkCyclicError("Combinational loop detected at runtime in {{{4}}} after 100 iters!")
    {1}
    {3}
    {2}
    # print( "SCC block{0} is executed", N, "times" )
    break
generated_block = wrapped_SCC_{0}
"""

      # clean up non-top variables if top is there. For slices of Bits
      # we directly use the top level wide Bits since Bits clone is
      # rpython code

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

      # also group them by common ancestor to reduce byte code
      # TODO use longest-common-prefix (LCP) algorithms ...

      final_var_host = defaultdict(list)
      for x in final_variables:
        final_var_host[ x.get_host_component() ].append( x )

      # Then, we generate the Python code that saves variables at the
      # beginning of each SCC iteration and the code that checks if the
      # values of those variables have changed
      copy_srcs  = []
      check_srcs = []

      var_id = 0
      for host, var_list in final_var_host.items():
        hostlen = len(repr(host))

        copy_srcs.append( f"host = {host!r}" )
        check_srcs.append( f"host = {host!r}" )

        sub_check_srcs = []

        for var in var_list:
          var_id += 1
          subname = repr(var)[hostlen+1:]
          if issubclass( var._dsl.Type, Bits ):     copy_srcs.append( f"t{var_id}=host.{subname}.clone()" )
          elif is_bitstruct_class( var._dsl.Type ): copy_srcs.append( f"t{var_id}=host.{subname}.clone()" )
          else:                                     copy_srcs.append( f"t{var_id}=deepcopy(host.{subname})" )

          sub_check_srcs.append( f"host.{subname} != t{var_id}" )

        check_srcs.append( f"if { ' or '.join(sub_check_srcs)}: continue" )

      # Divide all blks into meta blocks
      # Branchiness factor is the bound of branchiness in a meta block.
      branchiness_factor = 20
      branchy_block_factor = 6

      num_blks = 0  # sanity check
      cur_meta, cur_br, cur_count = [], 0, 0
      scc_schedule = []

      _globals = { 's': top, 'UpblkCyclicError': UpblkCyclicError }
      blk_srcs = []

      # If there is only 10 blocks, we directly unroll it
      if len(tmp_schedule) < 10:
        blk_srcs = []
        for i, b in enumerate(tmp_schedule):
          blk_srcs.append( f"blk{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
          _globals[f"blk{i}"] = b # put it into the block's closure

      else:
        for i, blk in enumerate( tmp_schedule ):
          # Same here. If an update block only has top-level loop, br = 0
          br = 0 if self.only_loop_at_top[blk] else self.branchiness[blk]
          if cur_br == 0:
            cur_meta.append( blk )
            cur_br += br
            cur_count += (br > 0)
            if cur_br >= branchiness_factor or cur_count >= branchy_block_factor:
              num_blks += len(cur_meta)
              scc_schedule.append( cur_meta )
              cur_meta, cur_br, cur_count = [], 0, 0 # clear
          else:
            if br == 0:
              # If no branchy block available, directly start a new metablock
              num_blks += len(cur_meta)
              scc_schedule.append( cur_meta )
              cur_meta, cur_br, cur_count = [ blk ], br, (br > 0)
            else:
              cur_meta.append( blk )
              cur_br += br
              cur_count += (br > 0)

              if cur_br + br >= branchiness_factor or cur_count + 1 >= branchy_block_factor:
                num_blks += len(cur_meta)
                scc_schedule.append( cur_meta )
                cur_meta, cur_br, cur_count = [], 0, 0 # clear

        if cur_meta:
          num_blks += len(cur_meta)
          scc_schedule.append( cur_meta )

        assert num_blks == len(tmp_schedule), f"Some blocks are missing during trace breaking of SCC "\
                                              f"({num_blks} compiled, {len(tmp_schedule)} total)"

        blk_srcs = []

        if len(scc_schedule) == 1:
          for i, b in enumerate( scc_schedule[-1] ):
            blk_srcs.append( f"blk{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
            _globals[ f"blk{i}" ] = b

        else:
          # TODO we might turn all meta blocks before the last one into meta
          # blocks, and directly fold the last block into the main loop
          # for i, meta in enumerate( scc_schedule[:-1] ):
            # b = self.compile_meta_block( meta )
            # blk_srcs.append( f"{b.__name__}()" )
            # _globals[ b.__name__ ] = b

          # for i, b in enumerate( scc_schedule[-1] ):
            # blk_srcs.append( f"blk_of_last_meta{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
            # _globals[ f"blk_of_last_meta{i}" ] = b

          for i, meta in enumerate( scc_schedule ):
            b = self.compile_meta_block( meta )
            blk_srcs.append( f"{b.__name__}()" )
            _globals[ b.__name__ ] = b


      scc_block_src = template.format( scc_id, "; ".join( copy_srcs ), "\n    ".join( check_srcs ),
                                       '\n    '.join(blk_srcs),
                                       ", ".join( [ x.__name__ for x in scc] ) )

      if _DEBUG: print(scc_block_src, "\n", "="*100 )

      _locals  = {}
      custom_exec(py.code.Source( scc_block_src ).compile(), _globals, _locals)
      return _locals[ 'generated_block' ]

    # Now we generate meta blocks for each SCC and produce final schedule

    constraint_objs = top._dag.constraint_objs

    # Perform topological sort on SCCs

    InD = { i: 0 for i in range(len(SCCs)) }
    nontrivial_sccs   = set()
    trivial_loop_sccs = set()

    for u, vs in G_new.items():
      # Preprocess some sets to mark non-trivial sccs and loop-only sccs
      # for later lookup
      if len(SCCs[u]) > 1:
        nontrivial_sccs.add( u )
      elif self.only_loop_at_top[ list(SCCs[u])[0] ]:
        trivial_loop_sccs.add( u )

      for v in vs:
        InD[ v ] += 1

    # Shunning: reuse this binary search from TraceBreakingPass. Not the
    # most efficient one. Ideally we want to use two heaps or a balanced
    # binary search tree ... TODO

    def insert_sortedlist( arr, key, item ):
      left, right = -1, len(arr)
      while left + 1 < right:
        mid = (left + right) >> 1
        if arr[mid][0] <= key:
          left = mid
        else:
          right = mid
      arr.insert( right, ( key, item ) )

    # scc_pred is for heuristic hamiltonian path ... It records for each
    # scc, in the schedule who is the predecessor that reduce its input
    # degree to zero.
    scc_pred = {}

    Q = []
    cnt = 0

    # Put the graph input nodes into the queue
    for v in range(len(SCCs)):
      if not InD[v]:
        cnt += 1
        scc_pred[v] = None
        if v in nontrivial_sccs or v in trivial_loop_sccs:
          insert_sortedlist( Q, (0, -cnt), v )
        else:
          insert_sortedlist( Q, (self.branchiness[list(SCCs[v])[0]], -cnt), v )

    schedule = []

    # Branchiness factor is the bound of branchiness in a meta block.
    branchiness_factor = 20

    # Block factor is the bound of the number of branchy blocks in a
    # meta block.
    branchy_block_factor = 6

    # refactored code ...
    def expand_node( u ):
      nonlocal cnt
      for v in G_new[u]:
        InD[v] -= 1
        if not InD[v]:
          cnt += 1
          scc_pred[ v ] = u
          # Now we use (br, timestamp) as the key because we want to kind
          # of preserve DFS behavior on top of the branch priority
          # Basically we want to pop in a DFS order such that the variable
          # most recently written can directly feed into the next block
          if v in nontrivial_sccs or v in trivial_loop_sccs:
            insert_sortedlist( Q, (0, -cnt), v )
          else:
            insert_sortedlist( Q, (self.branchiness[list(SCCs[v])[0]], -cnt), v )

    # Run topological sort

    cur_meta = []
    cur_br = cur_count = 0

    while Q:
      if cur_br == 0:
        (br, _), u = Q.pop(0)

        cur_meta.append( compile_scc(u) )
        cur_br += br
        cur_count += (br > 0)

        if cur_br >= branchiness_factor:
          schedule.append( cur_meta )
          cur_meta, cur_br, cur_count = [], 0, 0

      else:
        (br, _), u = Q.pop()

        # If no branchy block available, directly start a new metablock
        if br == 0:
          schedule.append( cur_meta )
          cur_meta, cur_br, cur_count = [], 0, 0

          cur_meta.append( compile_scc(u) )

        # Limit the number of branchiness and number of branchy blocks
        else:
          cur_meta.append( compile_scc(u) )
          cur_br += br
          cur_count += (br > 0)

          if cur_br + br >= branchiness_factor or cur_count + 1 >= branchy_block_factor:
            schedule.append( cur_meta )
            cur_meta, cur_br, cur_count = [], 0, 0

      expand_node( u )

    if cur_meta:
      schedule.append( cur_meta )

    # Put the graph schedule to _sched
    top._sched.update_schedule = []

    # TODO Same as what we want to do for the last block in SCC, we might
    # be able to remove the overhead of the last block's call_assembler_r
    # since the tracing will end anyway. We compile all meta block except
    # for the last one, and directly fold the last meta block into the
    # main loop.
    # We might want to add some heuristics to switch between two modes
    # for i, meta in enumerate( schedule[:-1] ):
      # top._sched.update_schedule.append( self.compile_meta_block( meta ) )
    # for i, b in enumerate( schedule[-1] ):
      # top._sched.update_schedule.append( b )
      # if _DEBUG: print( f"blk_of_last_meta{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
    if len(schedule) == 1:
      for i, b in enumerate( schedule[0] ):
        top._sched.update_schedule.append( b )
        if _DEBUG: print( f"blk{i}() # [br {self.branchiness[b]}, loop {int(self.only_loop_at_top[b])}] {b.__name__}" )
    else:
      for i, meta in enumerate( schedule ):
        top._sched.update_schedule.append( self.compile_meta_block( meta ) )
