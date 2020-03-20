"""
========================================================================
SimpleTickPass.py
========================================================================
Generate a simple tick function (no Mamba techniques here)

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
from pymtl3.dsl import MethodPort
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError

# Shunning: We are aware of the problem that there may be multiple places
# that assembles the function for the user to tick the simulator.
# I think LLVM applies passes based on the order they are inserted to the
# pass manager. LLVM also has some local ordering mechanism to figure out
# the dependencies between passes. Currently we haven't got to the point
# where we have enough passes to manage, but we should keep this in mind.

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
    top.tick = SimpleTickPass.gen_tick_function( final_schedule )
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
