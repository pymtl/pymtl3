"""
========================================================================
VcdGenerationPass.py
========================================================================

Author : Shunning Jiang
Date   : May 29, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.BasePass import BasePass, PassMetadata

from .errors import PassOrderError

import time
import sys

#-----------------------------------------------------------------------
# _gen_vcd_symbol
#-----------------------------------------------------------------------
# Utility generator to create new symbols for each VCD signal.
# Code inspired by MyHDL 0.7.
# Shunning: I just reuse it from pymtl v2
def _gen_vcd_symbol():

  # Generate a string containing all valid vcd symbol characters
  _codechars = ''.join([chr(i) for i in range(33, 127)])
  _mod       = len(_codechars)

  # Function to map an integer n to a new vcd symbol
  def next_vcd_symbol(n):
    q, r = divmod(n, _mod)
    code = _codechars[r]
    while q > 0:
      q, r = divmod(q, _mod)
      code = _codechars[r] + code
    return code

  # Generator logic
  n = 0
  while 1:
    yield next_vcd_symbol(n)
    n += 1

#-----------------------------------------------------------------------
# write_vcd_signal_defs
#-----------------------------------------------------------------------
def write_vcd_signal_defs( o, model ):

  vcd_symbol = _gen_vcd_symbol()
  all_nets   = []

  # Inner utility function to perform recursive descent of the model.
  def recurse_models( model, level ):

    # Create a new scope for this module
    print( "$scope module {name} $end".format( name=model.name ), file=o )

    # Define all signals for this model.
    for i in model.get_ports() + model.get_wires():

      # Multiple signals may be collapsed into a single net in the
      # simulator if they are connected. Generate new vcd symbols per
      # net, not per signal as an optimization.
      net = i._signalvalue
      if not hasattr( net, '_vcd_symbol' ):
        net._vcd_symbol = vcd_symbol.next()
        net._vcd_is_clk = i.name == 'clk'
        all_nets.append( net )
      symbol = net._vcd_symbol

      print( "$var {type} {nbits} {symbol} {name} $end".format(
          type='reg', nbits=i.nbits, symbol=symbol, name=i.name,
      ), file=o )

    # Recursively visit all submodels.
    for submodel in model.get_submodules():
      recurse_models( submodel, level+1 )

    print( "$upscope $end", file=o )

  # Begin recursive descent from the top-level model.
  recurse_models( model, 0 )

  # Once all models and their signals have been defined, end the
  # definition section of the vcd and print the initial values of all
  # nets in the design.
  print( "$enddefinitions $end\n", file=o )
  for net in all_nets:
    print( "b{value} {symbol}".format(
        value=net.bin(), symbol=net._vcd_symbol,
    ), file=o )

  return all_nets

#-----------------------------------------------------------------------
# insert_vcd_callbacks
#-----------------------------------------------------------------------
# Add callbacks which write the vcd file for each net in the design.
def insert_vcd_callbacks( sim, nets ):

  # A utility function which creates callbacks that write a nets current
  # value to the vcd file. The returned callback function is a closure
  # which is executed by the simulator whenever the net's value changes.
  def create_vcd_callback( sim, net ):

    # Each signal writes its binary value and unique identifier to the
    # specified vcd file
    if not net._vcd_is_clk:
      cb = lambda: print( 'b%s %s\n' % (net.bin(), net._vcd_symbol),
                          file=sim.vcd )

    # The clock signal additionally must update the vcd time stamp
    else:
      cb = lambda: print( '#%s\nb%s %s\n' % (100*sim.ncycles+50*net.uint(),
                          net.bin(), net._vcd_symbol),
                          file=sim.vcd )

    # Return the callback
    return cb

  # For each net in the simulator, create a callback and register it with
  # the net to be fired whenever the value changes. We repurpose the
  # existing callback facilities designed for slices (these execute
  # immediately), rather than the default callback mechanism (these are
  # put on the event queue to execute later).
  for net in nets:
    net.register_slice( create_vcd_callback( sim, net ) )


class VcdGenerationPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule

    top._vcd = PassMetadata()

    self.append_vcd_func_to_schedule( top )

  def append_vcd_func_to_schedule( self, top ):

    top._vcd.vcd_file_name = str(top.__class__) + ".vcd"
    top._vcd.vcd_file = open( top._vcd.vcd_file_name, "w" )

    # Get vcd timescale

    try:                    vcd_timescale = top.vcd_timescale
    except AttributeError:  vcd_timescale = "10ps"

    # Print vcd header

    print( "$date\n    {}\n$end\n$version\n     PyMTL 3 (Mamba)\n$end\n"
           "$timescale {}\n$end\n".format( time.asctime(), vcd_timescale ),
           file=top._vcd.vcd_file )

    # Preprocessing some metadata

    vcd_symbols = _gen_vcd_symbol()

    component_signals = defaultdict(list)

    all_components = set()
    for x in top._dsl.all_signals:
      host = x.get_host_component()
      component_signals[ host ].append(x)

    all_value_nets = top.get_all_value_nets()

    net_symbol_mapping = [ vcd_symbols.next() for x in all_value_nets ]
    signal_net_mapping = {}

    for i in range(len(all_value_nets)):
      for x in all_value_nets[i][1]:
        signal_net_mapping[x] = i

    # Inner utility function to perform recursive descent of the model.
    # Shunning: I mostly follow v2's implementation

    def recurse_models( m ):

      # Create a new scope for this module
      print( "$scope module {name} $end".format( name=repr(m) ), file=top._vcd.vcd_file )

      # Define all signals for this model.
      for signal in component_signals[m]:
        # Multiple signals may be collapsed into a single net in the
        # simulator if they are connected. Generate new vcd symbols per
        # net, not per signal as an optimization.

        if signal in signal_net_mapping:
          net = i._signalvalue
        if not hasattr( net, '_vcd_symbol' ):
          net._vcd_symbol = vcd_symbol.next()
          net._vcd_is_clk = i.name == 'clk'
          all_nets.append( net )
        symbol = net._vcd_symbol

        print( "$var {type} {nbits} {symbol} {name} $end".format(
            type='reg', nbits=i.nbits, symbol=symbol, name=i.name,
        ), file=top._vcd.vcd_file )

      # Recursively visit all submodels.
      for submodel in model.get_child_components():
        recurse_models( submodel )

      print( "$upscope $end", file=top._vcd.vcd_file )

    # Begin recursive descent from the top-level model.
    recurse_models( top )

    # Once all models and their signals have been defined, end the
    # definition section of the vcd and print the initial values of all
    # nets in the design.
    print( "$enddefinitions $end\n", file=top._vcd.vcd_file )

    for net in all_nets:
      print( "b{value} {symbol}".format(
          value=net.bin(), symbol=net._vcd_symbol,
      ), file=o )
