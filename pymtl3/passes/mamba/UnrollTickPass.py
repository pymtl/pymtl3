"""
========================================================================
UnrollTickPass.py
========================================================================
Generate an unrolled tick function

Author : Shunning Jiang
Date   : Dec 26, 2018
"""

import py

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class UnrollTickPass( BasePass ):

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

  def __call__( self, top ):
    if not hasattr( top, "_sched" ):
      raise PassOrderError( "_sched" )
    if not hasattr( top._sched, "update_schedule" ):
      raise PassOrderError( "update_schedule" )
    if not hasattr( top._sched, "schedule_ff" ):
      raise PassOrderError( "schedule_ff" )
    if not hasattr( top._sched, "schedule_posedge_flip" ):
      raise PassOrderError( "schedule_posedge_flip" )

    # We assemble the final schedule from multiple sources of required
    # work to generate a tick function for simulation

    # Currently the tick order is:
    # [ ff, tracing, posedge, clear_cl_trace, update ]

    final_schedule = []
    # call ff blocks first
    final_schedule.extend( top._sched.schedule_ff )

    # no tracing

    # posedge flip
    final_schedule.extend( top._sched.schedule_posedge_flip )

    # advance cycle after posedge
    def generate_advance_sim_cycle( top ):
      def advance_sim_cycle():
        top.simulated_cycles += 1
      return advance_sim_cycle
    final_schedule.append( generate_advance_sim_cycle(top) )

    # execute all update blocks
    final_schedule.extend( top._sched.update_schedule )

    top.tick = UnrollTickPass.gen_tick_function( final_schedule )
    # reset sim_cycles
    top.simulated_cycles = 0
