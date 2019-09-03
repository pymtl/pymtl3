"""
========================================================================
VcdGenerationPass.py
========================================================================

Author : Shunning Jiang, Yanghui Ou, Peitian Pan
Date   : May 29, 2019
"""

import time
from collections import defaultdict
from copy import deepcopy

from pymtl3.datatypes.BitStruct import BitStruct
from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata

from .errors import PassOrderError


class VcdGenerationPass( BasePass ):

  def __call__( self, top ):

    # Check for dum_vcd flag
    if not hasattr( top, "dump_vcd" ):
      return
    if not top.dump_vcd:
      return

    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule

    top._vcd = PassMetadata()

    schedule.append( self.make_vcd_func( top, top._vcd ) )

  def make_vcd_func( self, top, vcdmeta ):

    if hasattr( top, "vcd_file_name" ):
      vcdmeta.vcd_file_name = str(top.vcd_file_name) + ".vcd"
    else:
      vcdmeta.vcd_file_name = str(top.__class__) + ".vcd"
    vcdmeta.vcd_file = open( vcdmeta.vcd_file_name, "w" )

    # Get vcd timescale

    try:                    vcd_timescale = top.vcd_timescale
    except AttributeError:  vcd_timescale = "10ps"

    # Print vcd header

    print( "$date\n    {}\n$end\n$version\n    PyMTL 3 (Mamba)\n$end\n"
           "$timescale {}\n$end\n".format( time.asctime(), vcd_timescale ),
           file=vcdmeta.vcd_file )

    # Utility generator to create new symbols for each VCD signal.
    # Code inspired by MyHDL 0.7.
    # Shunning: I just reuse it from pymtl v2

    def _gen_vcd_symbol():

      # Generate a string containing all valid vcd symbol characters
      _codechars = ''.join([chr(i) for i in range(33, 127)])
      _mod       = len(_codechars)

      # Generator logic
      n = 0
      while True:
        q, r = divmod(n, _mod)
        code = _codechars[r]
        while q > 0:
          q, r = divmod(q, _mod)
          code = _codechars[r] + code
        yield code
        n += 1

    # The actual dump_vcd function to be appended to _sched.
    # The framework will call this function without arguments, and therefore
    # I chose to monkey patch the data structure objects to the global
    # namespace of `dump_vcd`. This might be hacky but probably better than
    # compiling a million lines of code to a Python function (you will almost
    # certainly get a segfault from that).
    # TODO: make this less hacky? type check?

    def dump_vcd():
      s             = top
      vcd_file      = vcdmeta.vcd_file
      clock_net_idx = vcdmeta.clock_net_idx
      clock_symbol  = net_symbol_mapping[vcdmeta.clock_net_idx]
      next_neg_edge = 100*vcdmeta.sim_ncycles+50
      next_pos_edge = 100*vcdmeta.sim_ncycles+100

      try:
        # Dump VCD
        for i, _net in enumerate( trimmed_value_nets ):
          net = eval(str(_net[0]))
          if i != clock_net_idx:
            symbol = net_symbol_mapping[i]
            if '{' in symbol:
              symbol = symbol.replace('{', '{{')
            if '}' in symbol:
              symbol = symbol.replace('}', '}}')

            # If we encounter a BitStruct then dump it as a concatenation of
            # all fields.
            # TODO: treat each field in a BitStruct as a separate signal?

            net_bits = net.to_bits() if isinstance(net, BitStruct) else net
            try:
              if getattr( vcdmeta, f"last_{i}" ) != net_bits:
                value_str = net_bits.bin()
                print( f'b{value_str} {symbol}', file=vcd_file )
                setattr( vcdmeta, f"last_{i}", deepcopy( net_bits ) )
            except AttributeError as e:
              raise AttributeError('{}\n - {} becomes another type. Please check your code.'.format(e, net))
      except Exception:
        raise

      # Flop clock at the end of cycle
      print( '\n#{}\nb0b0 {}'.format(next_neg_edge, clock_symbol), file=vcd_file )
      # Flip clock of the next cycle
      print( '#{}\nb0b1 {}\n'.format(next_pos_edge, clock_symbol), file=vcd_file )
      vcdmeta.sim_ncycles += 1

    vcd_symbols = _gen_vcd_symbol()

    # Preprocess some metadata

    component_signals = defaultdict(set)

    all_components = set()

    # We only collect non-sliced leaf signals
    # TODO only collect leaf signals and for nested structs
    for x in top._dsl.all_signals:
      for y in x.get_leaf_signals():
        host = y.get_host_component()
        component_signals[ host ].add(y)

    # We pre-process all nets in order to remove all sliced wires because
    # they belong to a top level wire and we count that wire

    trimmed_value_nets = []
    vcdmeta.clock_net_idx = None

    # FIXME handle the case where the top level signal is in a value net
    for writer, net in top.get_all_value_nets():
      new_net = []
      for x in net:
        if not isinstance(x, Const) and not x.is_sliced_signal():
          new_net.append( x )
          if repr(x) == "s.clk":
            # Hardcode clock net because it needs to go up and down
            assert vcdmeta.clock_net_idx is None
            vcdmeta.clock_net_idx = len(trimmed_value_nets)

      if new_net:
        trimmed_value_nets.append( new_net )

    # Generate symbol for existing nets

    net_symbol_mapping = [ next(vcd_symbols) for x in trimmed_value_nets ]
    signal_net_mapping = {}

    for i in range(len(trimmed_value_nets)):
      for x in trimmed_value_nets[i]:
        signal_net_mapping[x] = i

    # Inner utility function to perform recursive descent of the model.
    # Shunning: I mostly follow v2's implementation

    # Vcd file takes a(0) instead of a[0]
    def vcd_mangle_name( name ):
      return name.replace('[','(').replace(']',')')

    def recurse_models( m, level ):

      # Special case the top level "s" to "top"

      my_name = m.get_field_name()
      if my_name == "s":
        my_name = "top"

      # Create a new scope for this module
      print( "{}$scope module {} $end".format( "    "*level,
              vcd_mangle_name( my_name ) ),
              file=vcdmeta.vcd_file )

      m_name = repr(m)

      # Define all signals for this model.
      for signal in component_signals[m]:

        # Multiple signals may be collapsed into a single net in the
        # simulator if they are connected. Generate new vcd symbols per
        # net, not per signal as an optimization.

        if signal in signal_net_mapping:
          net_id = signal_net_mapping[signal]
          symbol = net_symbol_mapping[net_id]
        else:
          # We treat this as a new net

          # Check if it's clock. Hardcode clock net
          if repr(signal) == "s.clk":
            assert vcdmeta.clock_net_idx is None
            vcdmeta.clock_net_idx = len(trimmed_value_nets)

          trimmed_value_nets.append( [ signal ] )
          signal_net_mapping[signal] = len(signal_net_mapping)
          symbol = next(vcd_symbols)
          net_symbol_mapping.append( symbol )

        # This signal can be a part of an interface so we have to
        # "subtract" host component's name from signal's full name
        # to get the actual name like enq.rdy
        # TODO struct
        signal_name = vcd_mangle_name( repr(signal)[ len(m_name)+1: ] )
        print( "{}$var {type} {nbits} {symbol} {name} $end".format( "    "*(level+1),
                type='reg', nbits=signal._dsl.Type.nbits, symbol=symbol, name= signal_name),
              file=vcdmeta.vcd_file )

      # Recursively visit all submodels.
      for child in m.get_child_components():
        recurse_models( child, level+1 )

      print( "{}$upscope $end".format("    "*level),
              file=vcdmeta.vcd_file )

    # Begin recursive descent from the top-level model.
    recurse_models( top, 0 )

    # Once all models and their signals have been defined, end the
    # definition section of the vcd and print the initial values of all
    # nets in the design.
    print( "$enddefinitions $end\n", file=vcdmeta.vcd_file )

    for i, net in enumerate(trimmed_value_nets):
      net_type_inst = net[0]._dsl.Type()

      # Convert bit struct to bits to get around lack of bit struct
      # support.
      if isinstance( net_type_inst, BitStruct ):
        net_type_inst = net_type_inst.to_bits()

      print( "b{value} {symbol}".format(
          value=net_type_inst.bin(), symbol=net_symbol_mapping[i],
      ), file=vcdmeta.vcd_file )

      # Set this to be the last cycle value
      setattr( vcdmeta, "last_{}".format(i), net_type_inst.bin() )

    # Now we create per-cycle signal value collect functions

    vcdmeta.sim_ncycles = 0

    # Flip clock for the first cycle
    print( '\n#0\nb0b1 {}\n'.format( net_symbol_mapping[ vcdmeta.clock_net_idx ] ),
           file=vcdmeta.vcd_file )

    # Give all ' and " characters a preceding backslash for .format
    for i, x in enumerate(net_symbol_mapping):
      net_symbol_mapping[i] = x.replace('\\', '\\\\').replace('\'','\\\'').replace('\"','\\\"')

    # Monkey-patch `top`, `net_symbol_mapping`, and `trimmed_value_nets`
    # to the global namespace of `dump_vcd`
    dump_vcd.__globals__.update({
      'top'                : top,
      'net_symbol_mapping' : net_symbol_mapping,
      'trimmed_value_nets' : trimmed_value_nets,
    })

    return dump_vcd
