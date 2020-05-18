"""
========================================================================
VcdGenerationPass.py
========================================================================

Author : Shunning Jiang, Yanghui Ou, Peitian Pan
Date   : Sep 8, 2019
"""

import time
from collections import defaultdict

from pymtl3.datatypes import Bits, concat
from pymtl3.dsl import Const, MetadataKey
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class VcdGenerationPass( BasePass ):

  # VcdGenerationPass pass public pass data

  #: vcd file name
  #:
  #: Type: ``str``; input
  #:
  #: Default value: ""
  vcd_file_name = MetadataKey(str)

  vcd_func = MetadataKey()

  def __call__( self, top ):
    if top.has_metadata( self.vcd_file_name ):
      vcd_file_name = top.get_metadata( self.vcd_file_name )

      if vcd_file_name is not None:
        assert not top.has_metadata( self.vcd_func )
        top.set_metadata( self.vcd_func, self.make_vcd_func( top, vcd_file_name ) )

  def make_vcd_func( self, top, vcd_file_name ):
    assert vcd_file_name is not None
    if vcd_file_name != "":
      vcd_file_name = str(vcd_file_name) + ".vcd"
    else:
      vcd_file_name = str(top.__class__.__name__) + ".vcd"

    vcd_file = open( vcd_file_name, "w" )

    # Get vcd timescale

    try:                    vcd_timescale = top.vcd_timescale
    except AttributeError:  vcd_timescale = "10ps"

    # Print vcd header

    print( "$date\n  {}\n$end\n$version\n  PyMTL 3 (Mamba)\n$end\n"
           "$timescale\n {}\n$end\n".format( time.asctime(), vcd_timescale ),
           file=vcd_file )

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

    vcd_symbols = _gen_vcd_symbol()

    # Preprocess some metadata

    component_signals = defaultdict(set)

    all_components = set()

    # We only collect top level signals, and squash bitstruct into a long
    # bits object
    for x in top._dsl.all_signals:
      if x.is_top_level_signal():
        host = x.get_host_component()
        component_signals[ host ].add( x )

    # We pre-process all nets in order to remove all sliced wires because
    # they belong to a top level wire and we count that wire

    trimmed_value_nets = []
    vcd_clock_net_idx = None

    # FIXME handle the case where the top level signal is in a value net
    for writer, net in top.get_all_value_nets():
      new_net = []
      for x in net:
        if not isinstance(x, Const) and x.is_top_level_signal():
          new_net.append( x )
          if repr(x) == "s.clk":
            # Hardcode clock net because it needs to go up and down
            assert vcd_clock_net_idx is None
            vcd_clock_net_idx = len(trimmed_value_nets)

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
      # signal names with colons in it silently fail gtkwave
      return name.replace('[','(').replace(']',')').replace(':', '__')

    def recurse_models( m, spaces ):
      nonlocal vcd_clock_net_idx, vcd_sim_ncycles

      # Special case the top level "s" to "top"

      my_name = m.get_field_name()
      if my_name == "s":
        my_name = "top"

      # Create a new scope for this module
      print( f"{spaces}$scope module {vcd_mangle_name(my_name)} $end",
             file=vcd_file )

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
            assert vcd_clock_net_idx is None
            vcd_clock_net_idx = len(trimmed_value_nets)

          # This is a signal whose connection is not captured by the
          # global net data structure. This might be a sliced signal or
          # a signal updated in an upblk. Creating a new net for it does
          # not hurt functionality.

          trimmed_value_nets.append( [ signal ] )
          signal_net_mapping[signal] = len(signal_net_mapping)
          symbol = next(vcd_symbols)
          net_symbol_mapping.append( symbol )

        # This signal can be a part of an interface so we have to
        # "subtract" host component's name from signal's full name
        # to get the actual name like enq.rdy
        # TODO struct
        signal_name = vcd_mangle_name( repr(signal)[ len(m_name)+1: ] )
        print( f"{spaces}  $var reg {signal._dsl.Type.nbits} {symbol} {signal_name} $end",
               file=vcd_file )

      # Recursively visit all submodels.
      for child in m.get_child_components():
        recurse_models( child, spaces+'  ' )

      print( f"{spaces}$upscope $end", file=vcd_file )

    # Begin recursive descent from the top-level model.
    recurse_models( top, '' )

    # Once all models and their signals have been defined, end the
    # definition section of the vcd and print the initial values of all
    # nets in the design.
    print( "$enddefinitions $end\n", file=vcd_file )

    # last_values is an array of values from the previous cycle

    last_values = [0 for _ in range(len(trimmed_value_nets))]

    for i, net in enumerate(trimmed_value_nets):
      # Convert everything to Bits to get around lack of bit struct support.
      # The first cycle VCD contains the default value
      bin_str = net[0]._dsl.Type().to_bits().bin()

      print( f"b{bin_str} {net_symbol_mapping[i]}", file=vcd_file )

      # Set this to be the last cycle value str
      last_values[i] = bin_str

    # Now we create per-cycle signal value collect functions

    vcd_sim_ncycles = 0

    # Separate clock net from normal nets ahead of time
    clock_symbol = net_symbol_mapping[ vcd_clock_net_idx ]

    net_details = [ ( trimmed_value_nets[i][0], net_symbol_mapping[i] )
                    for i in range(len(trimmed_value_nets))
                      if i != vcd_clock_net_idx ]

    # Flip clock for the first cycle
    print( '\n#0\nb0b1 {}\n'.format( clock_symbol ), file=vcd_file, flush=True )

    # Returns a dump_vcd function that is ready to be appended to _sched.
    # TODO: type check?

    # Adding this 's' argument is for eval to correctly evaluate 's.x'...
    # Python 3 destroys a lot of our hacks .. sigh

    def dump_vcd_inner( s ):
      nonlocal vcd_sim_ncycles

      for i, (signal, symbol) in enumerate( net_details ):

        # If we encounter a BitStruct then dump it as a concatenation of
        # all fields.
        # TODO: treat each field in a BitStruct as a separate signal?

        try:
          net_bits_bin = eval(repr(signal)).to_bits()
        except Exception as e:
          raise TypeError(f'{e}\n - {signal} becomes another type. Please check your code.')

        net_bits_bin_str = net_bits_bin.bin()
        # `last_value` is the string form of a Bits object in binary
        # e.g. '0b000' == Bits3(0).bin()
        # We store strings instead of values ...
        if last_values[i] != net_bits_bin_str:
          last_values[i] = net_bits_bin_str
          print( f'b{net_bits_bin_str} {symbol}', file=vcd_file )

      # Flop clock at the end of cycle
      next_neg_edge = 100 * vcd_sim_ncycles + 50
      print( f'\n#{next_neg_edge}\nb0b0 {clock_symbol}', file=vcd_file )

      # Flip clock of the next cycle
      next_pos_edge = next_neg_edge + 50
      print( f'#{next_pos_edge}\nb0b1 {clock_symbol}\n', file=vcd_file, flush=True )
      vcd_sim_ncycles += 1

    def gen_dump_vcd( s ):
      def dump_vcd():
        dump_vcd_inner( s )
      return dump_vcd

    return gen_dump_vcd( top )
