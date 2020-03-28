"""
========================================================================
UnrollTickPass.py
========================================================================
Generate an unrolled tick function

Author : Shunning Jiang
Date   : Dec 26, 2018
"""

import py

from pymtl3.dsl.Connectable import MethodPort
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError

from ..sim.PrepareSimPass import PrepareSimPass


class UnrollSimPass( PrepareSimPass ):

  @staticmethod
  def gen_tick_function( funclist ):

    # Berkin IlBeyi's recipe ( updated using f-strings and enumerate )
    strs = [ f"_{idx}_{x.__name__}()" for idx, x in enumerate( funclist ) ]

    gen_tick_src = """
def compile_unroll( schedule ):
  {}
  def unrolled():
    # The code below does the actual calling of update blocks.
    {}
  return unrolled
        """.format( ";".join( [ f"_{idx}_{x.__name__}=schedule[{idx}]"
                                for idx, x in enumerate( funclist ) ] ),
                       "\n    ".join( strs ) )

    l = {}
    exec(py.code.Source( gen_tick_src ).compile(), l)
    return l['compile_unroll']( funclist )

  # Override
  def create_sim_eval_comb( self, top ):
    # FIXME update_once? currently check if the design has method_port
    method_ports = top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) )

    if len(method_ports) == 0: # Pure RTL design, add eval_combinational
      sim_eval_combinational = self.gen_tick_function( top._sched.update_schedule )
    else:
      def sim_eval_combinational():
        raise NotImplementedError(f"top is not a pure RTL design. {'top'+repr(list(method_ports)[0])[1:]} is a method port.")

    top.sim_eval_combinational = sim_eval_combinational

  # Override
  def create_sim_tick( self, top ):
    final_schedule = []
    if not top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) ):
      # Pure RTL -- tick update blocks first
      final_schedule = top._sched.update_schedule[::]

    if self.print_line_trace and hasattr( top, 'line_trace' ):
      final_schedule.append( top.print_line_trace )
    final_schedule += self.collect_ff_funcs( top )
    final_schedule += top._sched.update_schedule
    final_schedule.append( top._sim.check_top_level_inports )
    top.sim_tick = self.gen_tick_function( final_schedule )
