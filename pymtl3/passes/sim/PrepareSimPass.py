"""
========================================================================
AddSimUtilFuncsPass.py
========================================================================

Author : Shunning Jiang
Date   : Jan 26, 2020
"""


from pymtl3.datatypes import Bits, b1
from pymtl3.dsl.Component import Component
from pymtl3.dsl.Connectable import Const, Interface, MethodPort, Signal
from pymtl3.dsl.NamedObject import NamedObject
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError

from .SimpleTickPass import SimpleTickPass


class PrepareSimPass( BasePass ):
  def __init__( self, print_line_trace=True, reset_active_high=True ):
    assert reset_active_high in [ True, False ]

    self.print_line_trace  = print_line_trace
    self.reset_active_high = reset_active_high

  def __call__( self, top ):
    if hasattr(top, "sim_reset"):
      raise AttributeError( "Please rename the attribute top.sim_reset")
    if hasattr(top, "print_line_trace"):
      raise AttributeError( "Please modify the attribute top.print_line_trace")

    top._sim = PassMetadata()

    print_line_trace = self.print_line_trace and hasattr( top, 'line_trace' )

    # create utils functions
    if print_line_trace:
      top.print_line_trace = self.create_print_line_trace( top )
    top.sim_cycle_count  = self.create_sim_cycle_count( top )

    # ff_funcs summarizes the execution at the clock edge
    ff_funcs = []
    # append tracing related work
    if hasattr( top, "_tracing" ):
      if hasattr( top._tracing, "vcd_func" ):
        ff_funcs.append( top._tracing.vcd_func )
      if hasattr( top._tracing, "collect_text_sigs" ):
        ff_funcs.append( top._tracing.collect_text_sigs )
    ff_funcs.extend( top._sched.schedule_ff )
    ff_funcs.extend( top._sched.schedule_posedge_flip )
    advance_func = self.create_advance_sim_cycle( top )
    ff_funcs.append( advance_func )
    # clear cl method flag
    if hasattr( top, "_tracing" ):
      if hasattr( top._tracing, "clear_cl_trace" ):
        ff_funcs.append( top._tracing.clear_cl_trace )

    # append tracing related work
    up_funcs = top._sched.update_schedule

    top.sim_reset = self.create_sim_reset( top, print_line_trace, self.reset_active_high,
                                           ff_funcs, up_funcs, advance_func )

    # FIXME update_once?
    # check if the design has method_port
    method_ports = top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) )

    if len(method_ports) == 0:
      # Pure RTL design, add eval_combinational
      top.sim_eval_combinational = SimpleTickPass.gen_tick_function( top._sched.update_schedule )
      # Tick schedule first
      final_schedule = top._sched.update_schedule[::]
    else:
      tmp = list(method_ports)[0]
      def sim_eval_combinational():
        raise NotImplementedError(f"top is not a pure RTL design. {'top'+repr(tmp)[1:]} is a method port.")
      top.sim_eval_combinational = sim_eval_combinational
      final_schedule = []

    if print_line_trace:
      final_schedule.append( top.print_line_trace )
    final_schedule += ff_funcs + up_funcs
    top.sim_tick = SimpleTickPass.gen_tick_function( final_schedule )

    self.create_lock_unlock_simulation( top )

    top.lock_in_simulation()

  @staticmethod
  # Simulation related APIs
  def create_sim_reset( top, print_line_trace, active_high,
                        ff_funcs, up_funcs, advance ):
    # Avoid creating a loop
    ff = SimpleTickPass.gen_tick_function( ff_funcs )
    up = SimpleTickPass.gen_tick_function( up_funcs )

    def sim_reset():
      if print_line_trace:
        print()
      advance()
      top.reset @= b1( active_high )
      up()
      if print_line_trace:
        print( f"{top._sim.simulated_cycles:3}r {top.line_trace()}" )
      ff()
      up()
      if print_line_trace:
        print( f"{top._sim.simulated_cycles:3}r {top.line_trace()}" )
      ff()
      top.reset @= b1( not active_high )
      up()
    return sim_reset

  # Simulation related APIs
  @staticmethod
  def create_print_line_trace( top ):
    def print_line_trace():
      print( f"{top._sim.simulated_cycles:3}: {top.line_trace()}" )
    return print_line_trace

  @staticmethod
  def create_advance_sim_cycle( top ):
    top._sim.simulated_cycles = 0
    def advance_sim_cycle():
      top._sim.simulated_cycles += 1
    return advance_sim_cycle

  @staticmethod
  def create_sim_cycle_count( top ):
    def sim_cycle_count():
      return top._sim.simulated_cycles
    return sim_cycle_count

  @staticmethod
  def create_lock_unlock_simulation( top ):

    def lock_in_simulation():
      top._check_called_at_elaborate_top( "lock_in_simulation" )

      # Basically we want to avoid @= between elements in the same net since
      # we now use @=.
      # - First pass creates whole bunch of signals
      signal_object_mapping = {}

      Q = [ (top, top) ]
      while Q:
        current_obj, host = Q.pop()
        if isinstance( current_obj, list ):
          for i, obj in enumerate( current_obj ):
            if isinstance( obj, Signal ):
              try:
                value = obj.default_value()
                if obj._dsl.needs_double_buffer:
                  value <<= value
              except Exception as e:
                raise type(e)(str(e) + f' happens at {obj!r}')

              current_obj[i] = value

              signal_object_mapping[ obj ] = (current_obj, i, True, value)

            elif isinstance( obj, Component ):
              Q.append( (obj, obj) )
            elif isinstance( obj, (Interface, list) ):
              Q.append( (obj, host) )

        elif isinstance( current_obj, NamedObject ):
          for i, obj in current_obj.__dict__.items():
            if i[0] == '_': continue

            if isinstance( obj, Signal ):
              try:
                value = obj.default_value()
                if obj._dsl.needs_double_buffer:
                  value <<= value
              except Exception as e:
                raise type(e)(str(e) + f' happens at {obj!r}')

              setattr( current_obj, i, value )
              signal_object_mapping[obj] = (current_obj, i, False, value)

            elif isinstance( obj, Component ):
              Q.append( (obj, obj) )
            elif isinstance( obj, (Interface, list) ):
              Q.append( (obj, host) )

      # Swap all Signal objects with actual data
      nets = top.get_all_value_nets()

      # First step is to consolidate all non-slice signals in the same net
      # by pointing them to the same object
      # TODO optimize for bitstruct fields. Essentially only sliced signals
      # should be excluded.

      for writer, signals in nets:
        residence = None

        # Find the residence value
        if isinstance( writer, Const ) or writer.is_top_level_signal():
          residence = writer
        else:
          for x in signals:
            if x.is_top_level_signal():
              residence = x
              break

        if residence is None:
          continue # whole net is slice

        if isinstance( residence, Const ):
          residence_value = residence._dsl.const
        else:
          residence_value = signal_object_mapping[ residence ][-1]

        # Replace top-level signals in the net with residence value

        for x in signals:
          if x is not residence and x.is_top_level_signal():
            # swap old value with new residence value

            current_obj, i, is_list, value = signal_object_mapping[ x ]
            signal_object_mapping[ x ] = (current_obj, i, is_list, residence_value)

            if is_list:
              current_obj[i] = residence_value
            else:
              setattr( current_obj, i, residence_value )

      top._sim.signal_object_mapping = signal_object_mapping
      top._sim.locked_simulation = True

    def unlock_simulation():
      top._check_called_at_elaborate_top( "unlock_simulation" )
      try:
        assert top._sim.locked_simulation
      except:
        raise AttributeError("Cannot unlock an unlocked/never locked model.")

      top._sim.unlocked_simulation = True
      top._sim.locked_simulation = False

      # We will reuse the same Bits object since they won't change anymore
      for obj, (current_obj, i, is_list, _) in top._sim.signal_object_mapping.items():
        if is_list: current_obj[i] = obj
        else:       setattr( current_obj, i, obj )

    top.lock_in_simulation = lock_in_simulation
    top.unlock_simulation  = unlock_simulation
