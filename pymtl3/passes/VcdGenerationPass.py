"""
========================================================================
VcdGenerationPass.py
========================================================================

Author : Shunning Jiang, Yanghui Ou, Peitian Pan
Date   : Sep 8, 2019
"""

import time
from collections import defaultdict

from pymtl3.datatypes import Bits, is_bitstruct_class, is_bitstruct_inst
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

    # Given top, net_symbol_mapping, trimmed_value_nets, last_values, `make_dump_vcd`
    # returns a dump_vcd function that is ready to be appended to _sched.
    # TODO: type check?

    def make_dump_vcd( top, net_symbol_mapping, trimmed_value_nets, last_values ):

      def dump_vcd():
        s             = top
        vcd_file      = vcdmeta.vcd_file
        clock_net_idx = vcdmeta.clock_net_idx
        clock_symbol  = net_symbol_mapping[clock_net_idx]
        next_neg_edge = 100*vcdmeta.sim_ncycles+50
        next_pos_edge = 100*vcdmeta.sim_ncycles+100
        gd, ld        = globals(), locals()
        evaled_nets   = [eval(str(net[0]), gd, ld) for net in trimmed_value_nets]

        try:
          # Dump VCD
          for i, net in enumerate( evaled_nets ):
            if i != clock_net_idx:
              symbol = net_symbol_mapping[i]

              # If we encounter a BitStruct then dump it as a concatenation of
              # all fields.
              # TODO: treat each field in a BitStruct as a separate signal?

              net_bits = to_bits(net) if is_bitstruct_inst( net ) else net
              try:
                # `last_value` is the string form of a Bits object in binary
                # e.g. '0b000' == Bits3(0).bin()
                last_value = last_values[i]
                if last_value != net_bits:
                  if not hasattr(net_bits, "bin"):
                    # Probably an integer instead of a Bits. Try to infer its
                    # bitwidth from its last occurrence...
                    net_bits = Bits(len(last_value)-2, net_bits)
                  value_str = net_bits.bin()
                  print( f'b{value_str} {symbol}', file=vcd_file )
                  last_values[i] = value_str
              except AttributeError as e:
                raise AttributeError(f'{e}\n - {net} becomes another type. Please check your code.')
        except Exception:
          raise

        # Flop clock at the end of cycle
        print( f'\n#{next_neg_edge}\nb0b0 {clock_symbol}', file=vcd_file )
        # Flip clock of the next cycle
        print( f'#{next_pos_edge}\nb0b1 {clock_symbol}\n', file=vcd_file, flush=True )
        vcdmeta.sim_ncycles += 1

      return dump_vcd

    vcd_symbols = _gen_vcd_symbol()

    # Preprocess some metadata

    component_signals = defaultdict(set)

    all_components = set()

    # We only collect non-sliced leaf signals
    # TODO only collect leaf signals and for nested structs
    for x in top._dsl.all_signals:
      if x.is_leaf_signal():
        for y in x.get_leaf_signals():
          host = y.get_host_component()
          component_signals[ host ].add(y)
      else:
        # BitStruct signals are not leaf signals. We just add the whole vector
        # to the component_signals dict instead of adding all fields
        host = x.get_host_component()
        component_signals[ host ].add(x)

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
      # signal names with colons in it silently fail gtkwave
      return name.replace('[','(').replace(']',')').replace(':', '__')

    def get_nbits( Type ):
      try:
        return Type.nbits
      except AttributeError:
        assert is_bitstruct_class( Type ), f"{Type} is not a valid PyMTL type!"
        return sum(get_nbits(v) for v in Type.__bitstruct_fields__.values())

    def to_bits( obj ):
      # BitsN
      if isinstance( obj, Bits ):
        return obj
      # BitStruct
      bits = [to_bits(getattr(obj, v)) for v in obj.__bitstruct_fields__.keys()]
      for _bits in bits[1:]:
        bits[0] = (bits[0] << _bits.nbits) | _bits
      return bits[0]

    def recurse_models( m, level ):

      # Special case the top level "s" to "top"

      my_name = m.get_field_name()
      if my_name == "s":
        my_name = "top"

      # Create a new scope for this module
      print( f"{'    '*level}$scope module {vcd_mangle_name(my_name)} $end",
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
        print( f"{'    '*(level+1)}$var 'reg' {get_nbits(signal._dsl.Type)} {symbol} {signal_name} $end",
               file=vcdmeta.vcd_file )

      # Recursively visit all submodels.
      for child in m.get_child_components():
        recurse_models( child, level+1 )

      print( f"{'    '*level}$upscope $end", file=vcdmeta.vcd_file )

    # Begin recursive descent from the top-level model.
    recurse_models( top, 0 )

    # Once all models and their signals have been defined, end the
    # definition section of the vcd and print the initial values of all
    # nets in the design.
    print( "$enddefinitions $end\n", file=vcdmeta.vcd_file )

    # vcdmeta.last_values is an array of values from the previous cycle
    vcdmeta.last_values = [0 for _ in range(len(trimmed_value_nets))]
    last_values         = vcdmeta.last_values

    for i, net in enumerate(trimmed_value_nets):
      net_type_inst = net[0]._dsl.Type()

      # Convert bit struct to bits to get around lack of bit struct
      # support.
      if is_bitstruct_inst( net_type_inst ):
        net_type_inst = to_bits( net_type_inst )

      print( f"b{net_type_inst.bin()} {net_symbol_mapping[i]}", file=vcdmeta.vcd_file )

      # Set this to be the last cycle value
      last_values[i] = net_type_inst.bin()

    # Now we create per-cycle signal value collect functions

    vcdmeta.sim_ncycles = 0

    # Flip clock for the first cycle
    print( '\n#0\nb0b1 {}\n'.format( net_symbol_mapping[ vcdmeta.clock_net_idx ] ),
           file=vcdmeta.vcd_file, flush=True )

    return make_dump_vcd(top, net_symbol_mapping, trimmed_value_nets, last_values)
