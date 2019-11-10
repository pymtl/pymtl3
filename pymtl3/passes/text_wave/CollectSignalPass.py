"""
========================================================================
CollectSignalPass.py
========================================================================
collects signals and stored it as _collect_signals attribute of top.

Author : Kaishuo Cheng, Shunning Jiang
Date   : Nov 9, 2019
"""

from collections import defaultdict
from copy import deepcopy

import py

from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata

from ..errors import PassOrderError


class CollectSignalPass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule

    try:
      en = top.text_wave
    except AttributeError:
      return

    if en:
      top._textwave = PassMetadata()
      schedule.append( self.collect_sig_func( top, top._textwave ) )

  def collect_sig_func( self, top, wavmeta ):
    component_signals = defaultdict(set)
    all_components = set()
    for x in top._dsl.all_signals:
      for y in x.get_leaf_signals():
        host = y.get_host_component()
        component_signals[ host ].add( y )

    # We pre-process all nets in order to remove all sliced wires because
    # they belong to a top level wire and we count that wire

    trimmed_value_nets = []
    wavmeta.clock_net_idx = None

    # FIXME handle the case where the top level signal is in a value net
    for writer, net in top.get_all_value_nets():
      new_net = []
      for x in net:
        if not isinstance(x, Const) and not x.is_sliced_signal():
          new_net.append( x )
          if repr(x) == "s.clk":
            # Hardcode clock net because it needs to go up and down
            assert wavmeta.clock_net_idx is None
            wavmeta.clock_net_idx = len(trimmed_value_nets)

      if new_net:
        trimmed_value_nets.append( new_net )

    # Inner utility function to perform recursive descent of the model.
    # Shunning: I mostly follow v2's implementation

    def recurse_models( m, level ):

      # Special case the top level "s" to "top"

      my_name = m.get_field_name()
      if my_name == "s":
        my_name = "top"

      m_name = repr(m)

      # Define all signals for this model.
      for signal in component_signals[m]:
        trimmed_value_nets.append( [ signal ] )

      # Recursively visit all submodels.
      for child in m.get_child_components():
        recurse_models( child, level+1 )

    # Begin recursive descent from the top-level model.

    recurse_models( top, 0 )

    # Now we create per-cycle signal value collect functions

    dump_wav_per_signal = "wavmeta.sigs['{0}'].append( {0}.bin() )"

    # Concatenate the strings for all signals

    # Give all ' and " characters a preceding backslash for .format
    wav_srcs = []
    for i, net in enumerate( trimmed_value_nets ):
      if i != wavmeta.clock_net_idx:
        wav_srcs.append( dump_wav_per_signal.format( net[0]) )
    deepcopy # I have to do this to circumvent the tools
    wavmeta.sigs = defaultdict(list)

    # TODO use integer index instead of dict, should be easy
    src =  """
def dump_wav():
  {}
""".format( "\n  ".join(wav_srcs) )
    s, l_dict = top, {}
    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)
    return l_dict['dump_wav']
