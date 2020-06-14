"""
========================================================================
DumpUDGPass.py
========================================================================

Author : Shunning Jiang
Date   : June 15, 2020
"""
from graphviz import Digraph

from pymtl3.dsl import CalleePort

from ..BasePass import BasePass


class DumpUDGPass( BasePass ):

  def __call__( self, top ):
    if not hasattr(top, "_udg"):
      raise PassOrderError( "_udg" )
    if not hasattr( top._udg, "all_constraints" ):
      raise PassOrderError( "all_constraints" )

    V = top.get_all_update_blocks()
    ff = top.get_all_update_ff()
    E = top._udg.all_constraints
    self.dump_udg( top, V, ff, E )

  def dump_udg( self, top, V, ff, E ):
    print("[DumpUDGPass] Making plots ...\n")
    dot = Digraph()
    dot.graph_attr["rank"] = "same"
    dot.graph_attr["ratio"] = "compress"
    dot.graph_attr["margin"] = "0.1"

    for x in V:
      x_name = repr(x) if isinstance( x, CalleePort ) else x.__name__
      if x in ff:
        x_name += "_FF"
      try:
        x_host = repr(x.get_parent_object() if isinstance( x, CalleePort )
                      else top.get_update_block_host_component(x))
      except:
        x_host = ""
      dot.node( x_name +"\\n@" + x_host, shape="box")

    for (x, y) in E:
      x_name = repr(x) if isinstance( x, CalleePort ) else x.__name__
      if x in ff:
        x_name += "_FF"
      try:
        x_host = repr(x.get_parent_object() if isinstance( x, CalleePort )
                      else top.get_update_block_host_component(x))
      except:
        x_host = ""
      y_name = repr(y) if isinstance( y, CalleePort ) else y.__name__
      if y in ff:
        y_name += "_FF"
      try:
        y_host = repr(y.get_parent_object() if isinstance( y, CalleePort )
                      else top.get_update_block_host_component(y))
      except:
        y_host = ""

      dot.edge( x_name+"\\n@"+x_host, y_name+"\\n@"+y_host )
    dot.render( f"{top.__class__.__name__}-udg.gv", view=True )
