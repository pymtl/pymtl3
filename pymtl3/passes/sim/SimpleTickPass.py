"""
========================================================================
SimpleTickPass.py
========================================================================
Generate a simple tick function (no Mamba techniques here)

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class SimpleTickPass( BasePass ):

  @staticmethod
  def gen_tick_function( schedule ):
    def iterative():
      for blk in schedule:
        blk()
    return iterative

  def __call__( self, top ):
    if not hasattr( top._sched, "update_schedule" ):
      raise PassOrderError( "update_schedule" )

    # We assemble the final schedule from multiple sources of required
    # work to generate a tick function for simulation

    # Currently the tick order is:
    # [ ff, tracing, posedge, clear_cl_trace, update ]

    final_schedule = []
    # call ff blocks first
    final_schedule.extend( top._sched.schedule_ff )

    # append tracing related work

    if hasattr( top._tracing, "vcd_func" ):
      final_schedule.append( top._tracing.vcd_func )
    if hasattr( top._tracing, "collect_text_sigs" ):
      final_schedule.append( top._tracing.collect_text_sigs )

    # posedge flip
    final_schedule.extend( top._sched.schedule_posedge_flip )

    # execute all update blocks
    final_schedule.extend( top._sched.update_schedule )

    # Generate tick
    top.tick = SimpleTickPass.gen_tick_function( final_schedule )
    # FIXME update_once?
    top.eval_combinational = SimpleTickPass.gen_tick_function( top._sched.update_schedule )
