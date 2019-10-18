"""
========================================================================
HeuristicTopo.py
========================================================================

Author : Shunning Jiang
Date   : Dec 26, 2018
"""

import ast
from queue import PriorityQueue

from graphviz import Digraph

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError
from pymtl3.passes.SimpleSchedulePass import check_schedule


class CountBranches( ast.NodeVisitor ):

  def enter( self, node ):
    self.num_br = 0
    self.visit( node )
    return self.num_br

  def visit_If( self, node ):
    self.num_br += 1
    self.visit( node.test )

    for stmt in node.body:
      self.visit( stmt )

    for stmt in node.orelse:
      self.visit( stmt )

  def visit_IfExp( self, node ):
    self.num_br += 1
    self.visit( node.test )
    self.visit( node.body )
    self.visit( node.orelse )

  # A single for is estimated to be 10x of a branch
  def visit_For( self, node ):
    self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )

  def visit_While( self, node ):
    self.num_br += 0
    for stmt in node.body:
      self.visit( stmt )

class HeuristicTopoPass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._dag, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    top._sched = PassMetadata()

    top._sched.schedule = self.schedule( top )

  def schedule( self, top ):

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

    # Perform topological sort for a serial schedule.
    # Note that here we use a priority queue to get the blocks with small
    # branchiness as early as possible

    schedule = []

    # Python3 doesn't have hash for functions
    id_v = { id(v): v for v in V}

    Q = PriorityQueue(0)
    for v in V:
      if not InD[v]:
        Q.put( (branchiness[ v ], id(v)) )

    while not Q.empty():
      br, u = Q.get()
      schedule.append( id_v[u] )
      for v in Es[id_v[u]]:
        InD[v] -= 1
        if not InD[v]:
          Q.put( (branchiness[ v ], id(v)) )

    check_schedule( top, schedule, V, E, InD )

    return schedule
