"""
========================================================================
HeuristicTopo.py
========================================================================

Author : Shunning Jiang
Date   : Feb 14, 2020
"""

import ast
from queue import PriorityQueue

from ..BasePass import BasePass, PassMetadata
from ..errors import PassOrderError
from ..sim.SimpleSchedulePass import SimpleSchedulePass, check_schedule
from .UnrollSimPass import UnrollSimPass

# FIXME also apply branchiness to all update_ff blocks

# Shunning feb-14-2020: This CountBranchesLoops is enhanced to recognize
# if a block only has loop at the top. So we found that a loop actually
# trace-breaks itselfs by calling call_assembler_r and return after the
# execution is complete. This means loops are totally different from
# branches.

class CountBranchesLoops( ast.NodeVisitor ):

  def enter( self, node ):
    self.num_br = 0
    self.loop_stack = 0
    self.only_loop_at_top = False
    self.visit( node )
    return self.num_br, self.only_loop_at_top

  def visit_FunctionDef( self, node ):
    for stmt in node.body:
      self.only_loop_at_top |= isinstance( stmt, (ast.For, ast.While) )

    for stmt in node.body:
      self.visit( stmt )

    if node.returns:
      for expr in node.returns:
        self.visit( expr )

  def visit_If( self, node ):
    self.only_loop_at_top &= (self.loop_stack > 0)

    # Special case "if s.reset:" -- it's only high for a cycle
    if isinstance( node.test, ast.Attribute ) and \
       node.test.attr == 'reset' and \
       isinstance( node.test.value, ast.Name ) and \
       node.test.value.id == 's':
      pass
    else:
      self.num_br += 1
    self.visit( node.test )

    for stmt in node.body:
      self.visit( stmt )

    for stmt in node.orelse:
      self.visit( stmt )

  def visit_IfExp( self, node ):
    self.only_loop_at_top &= (self.loop_stack > 0)

    # Special case "if s.reset:" -- it's only high for a cycle
    if isinstance( node.test, ast.Attribute ) and \
       node.test.attr == 'reset' and \
       isinstance( node.test.value, ast.Name ) and \
       node.test.value.id == 's':
      pass
    else:
      self.num_br += 1

    self.visit( node.test )
    self.visit( node.body )
    self.visit( node.orelse )

  # For/while is fine
  def visit_For( self, node ):
    self.loop_stack += 1
    # self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )
    self.loop_stack -= 1

  def visit_While( self, node ):
    self.loop_stack += 1
    # self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )
    self.loop_stack -= 1

class HeuristicTopoPass( UnrollSimPass ):
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

    top._sim = PassMetadata()

    self.create_print_line_trace( top )
    self.create_sim_cycle_count( top )
    self.create_lock_unlock_simulation( top )
    top.lock_in_simulation()

    self.create_sim_eval_comb( top )
    self.create_sim_tick( top )
    self.create_sim_reset( top )

  def schedule_intra_cycle( self, top ):

    # Construct the intra-cycle graph based on normal update blocks

    V   = top._dag.final_upblks - top.get_all_update_ff()
    E   = set()
    Es  = { v: [] for v in V }
    InD = { v: 0  for v in V }

    for (u, v) in top._dag.all_constraints: # u -> v
      if u in V and v in V:
        InD[v] += 1
        Es[u].append( v )
        E.add( (u, v) )

    # Extract branchiness

    # Initialize all generated net block to 0 branchiness
    branchiness = { x: 0 for x in top._dag.genblks }

    visitor = CountBranchesLoops()
    # FIXME use the pure-loop info
    for blk in top.get_all_update_blocks():
      hostobj = top.get_update_block_host_component( blk )
      branchiness[ blk ], _ = visitor.enter( hostobj.get_update_block_info( blk )[-1] )

    # Perform topological sort for a serial schedule.
    # Note that here we use a priority queue to get the blocks with small
    # branchiness as early as possible

    top._sched.update_schedule = update_schedule = []

    # Python3 doesn't have hash for functions
    id_v = { id(v): v for v in V}

    Q = PriorityQueue(0)
    for v in V:
      if not InD[v]:
        Q.put( (branchiness[ v ], id(v)) )

    while not Q.empty():
      br, u = Q.get()
      update_schedule.append( id_v[u] )
      for v in Es[id_v[u]]:
        InD[v] -= 1
        if not InD[v]:
          Q.put( (branchiness[ v ], id(v)) )

    check_schedule( top, update_schedule, V, E, InD )
