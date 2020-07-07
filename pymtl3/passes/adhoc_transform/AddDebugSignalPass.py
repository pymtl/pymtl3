"""
========================================================================
AddDebugSignalPass.py
========================================================================
TODO currently doesn't support array of components because the uniquification
of added signal names of an array of components is very convoluted.
The verilog translation support is limited for two components of the
same class that have different names of debug signals.

Author : Shunning Jiang
Date   : Jul 5, 2020
"""

from pymtl3.dsl import Component, InPort, MetadataKey, OutPort
from pymtl3.passes.BasePass import BasePass


class AddDebugSignalPass( BasePass ):

  debug_pins = MetadataKey(set)

  def __call__( self, top, signal_names ):

    s_signal_names = []
    for name in signal_names:
      assert name.startswith("top.")
      assert '[' not in name, "Currently don't support any array of components"
      s_signal_names.append( f"s{name[3:]}")

    signals = sorted( top.get_all_object_filter( lambda x: repr(x) in s_signal_names ),
                      key=repr )

    for i, signal in enumerate( signals ):
      debug_pin_name = f"debug_{i}"
      last_port = signal
      host = signal.get_host_component()
      while host is not None:
        this_port = OutPort( last_port.get_type() )
        top.add_value_port( host, debug_pin_name, this_port )
        top.add_connection( this_port, last_port )
        last_port = this_port
        host = host.get_parent_object()
