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
from pymtl3.passes.sim.SimpleTickPass import SimpleTickPass


class UnrollTickPass( BasePass ):

  @staticmethod
  def gen_tick_function( schedule ):

    # Berkin IlBeyi's recipe ( updated using f-strings and enumerate )
    strs = [f"  update_blk{idx}() # {sched}" for idx, sched in \
        enumerate([ x.__name__ for x in schedule ])]

    gen_tick_src = """
        def compile_unroll( schedule ):
          {}
          def tick_unroll():
            # The code below does the actual calling of update blocks.
          {}
          return tick_unroll
        """.format( ";".join( map(
                        "update_blk{0}=schedule[{0}]".format,
                        range( len( schedule ) ) ) ),
                        "\n          ".join( strs ) )

    l = {}
    exec(py.code.Source( gen_tick_src ).compile(), l)
    # print(gen_tick_src)
    return l['compile_unroll']( schedule )

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
