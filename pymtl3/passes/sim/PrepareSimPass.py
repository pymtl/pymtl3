"""
========================================================================
AddSimUtilFuncsPass.py
========================================================================

Author : Shunning Jiang
Date   : Jan 26, 2020
"""

import py

from pymtl3.datatypes import Bits, b1
from pymtl3.dsl.Component import Component
from pymtl3.dsl.Connectable import Const, Interface, MethodPort, Signal
from pymtl3.dsl.NamedObject import NamedObject
from pymtl3.extra.pypy import custom_exec
from pymtl3.passes.backends.verilog import VerilogTBGenPass
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError
from pymtl3.passes.tracing.CLLineTracePass import CLLineTracePass
from pymtl3.passes.tracing.LineTraceParamPass import LineTraceParamPass
from pymtl3.passes.tracing.PrintTextWavePass import PrintTextWavePass
from pymtl3.passes.tracing.VcdGenerationPass import VcdGenerationPass

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
    if not hasattr( top, "_sched" ):
      raise PassOrderError( "_sched" )
    if not hasattr( top._sched, "update_schedule" ):
      raise PassOrderError( "update_schedule" )
    if not hasattr( top._sched, "schedule_ff" ):
      raise PassOrderError( "schedule_ff" )
    if not hasattr( top._sched, "schedule_posedge_flip" ):
      raise PassOrderError( "schedule_posedge_flip" )

    top._sim = PassMetadata()

    self.create_print_line_trace( top )
    self.create_sim_cycle_count( top )
    self.create_lock_unlock_simulation( top )

    top.lock_in_simulation()

    self.create_sim_eval_comb( top )
    self.create_sim_tick( top )
    self.create_sim_reset( top )


  def create_sim_eval_comb( self, top ):
    # Pure RTL design, add eval_combinational
    if len( top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) ) ) == 0 and \
       len( top.get_all_update_once() ) == 0:
      sim_eval_combinational = SimpleTickPass.gen_tick_function( [top._sim.check_top_level_inports] + top._sched.update_schedule )
    else:
      def sim_eval_combinational():
        raise NotImplementedError(f"top is not a pure RTL design. {'top'+repr(list(method_ports)[0])[1:]} is a method port.")

    top.sim_eval_combinational = sim_eval_combinational

  def create_sim_tick( self, top ):
    final_schedule = []

    # Pure RTL -- tick update blocks first
    if len( top.get_all_object_filter( lambda x: isinstance( x, MethodPort ) ) ) == 0 and \
       len( top.get_all_update_once() ) == 0:
      final_schedule = top._sched.update_schedule[::]

    if self.print_line_trace and hasattr( top, 'line_trace' ):
      final_schedule.append( top.print_line_trace )
    final_schedule += self.collect_ff_funcs( top )
    final_schedule += top._sched.update_schedule
    final_schedule.append( top._sim.check_top_level_inports )
    top.sim_tick = SimpleTickPass.gen_tick_function( final_schedule )

  def collect_ff_funcs( self, top ):
    # ff_funcs summarizes the execution at the clock edge
    ret = []
    # append tracing related work
    if top.has_metadata( VcdGenerationPass.vcd_func ):
      ret.append( top.get_metadata( VcdGenerationPass.vcd_func ) )

    if top.has_metadata( PrintTextWavePass.textwave_func ):
      ret.append( top.get_metadata( PrintTextWavePass.textwave_func ) )

    if top.has_metadata( VerilogTBGenPass.vtbgen_hooks ):
      ret.extend( top.get_metadata( VerilogTBGenPass.vtbgen_hooks ) )

    ret.extend( top._sched.schedule_ff )
    ret.extend( top._sched.schedule_posedge_flip )
    ret.append( self.create_advance_sim_cycle( top ) )

    # clear cl method flag after flip
    if top.has_metadata( CLLineTracePass.clear_cl_trace_func ):
      ret.append( top.get_metadata( CLLineTracePass.clear_cl_trace_func ) )

    return ret

  # Simulation related APIs
  def create_sim_reset( self, top ):
    ff = SimpleTickPass.gen_tick_function( self.collect_ff_funcs( top ) )
    up = SimpleTickPass.gen_tick_function( top._sched.update_schedule )

    print_line_trace = self.print_line_trace and hasattr( top, 'line_trace' )
    active_high      = self.reset_active_high

    def sim_reset():
      if print_line_trace:
        print()
      # cycle 0
      top.reset @= b1( active_high )
      up()

      ff()
      # cycle 1
      up()
      if print_line_trace:
        print( f"{top._sim.simulated_cycles:3}r {top.line_trace()}" )

      ff()
      # cycle 2
      up()
      if print_line_trace:
        print( f"{top._sim.simulated_cycles:3}r {top.line_trace()}" )

      ff()
      # cycle 3
      top.reset @= b1( not active_high )
      up()

    top.sim_reset = sim_reset

  def create_print_line_trace( self, top ):
    if self.print_line_trace and hasattr( top, 'line_trace' ):
      def print_line_trace():
        print( f"{top._sim.simulated_cycles:3}: {top.line_trace()}" )
      top.print_line_trace = print_line_trace

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
    top.sim_cycle_count = sim_cycle_count

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

      # Add the function that checks if the Bits objects of
      # top-level input ports are modified. If so, it's mostly because
      # the top-level ports are assigned with = instead of @=.

      inports = []
      objs    = []
      for x in top._dsl.all_signals:
        if x.is_input_value_port() and x.is_top_level_signal() and x.get_host_component() is top:
          inports.append( x )
          objs.append( signal_object_mapping[x][-1] )

      src = """
def check_top_level_inports():
  {}
""".format( "\n  ".join([ f"assert {x} is obj{i}, 'Please use @= to assign top level InPort top.{repr(x)[2:]}'"
                            for i, x in enumerate(inports) ]) )
      _locals = {}
      _globals = { f"obj{i}" : x for i, x in enumerate(objs) }
      _globals['s'] = top
      custom_exec( py.code.Source(src).compile(), _globals, _locals)
      top._sim.check_top_level_inports = _locals['check_top_level_inports']

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
