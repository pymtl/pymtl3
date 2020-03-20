"""
========================================================================
CollectSignalPass.py
========================================================================
collects signals and stored it as _collect_signals attribute of top.

Author : Kaishuo Cheng, Shunning Jiang
Date   : Nov 9, 2019
"""

from collections import defaultdict

import py

from pymtl3.datatypes import Bits, is_bitstruct_class, to_bits
from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import ModelTypeError, PassOrderError


class CollectSignalPass( BasePass ):
  def __call__( self, top ):
    if hasattr( top, "config_tracing" ):
      top.config_tracing.check()

      if top.config_tracing.tracing in [ 'text_ascii', 'text_fancy' ]:
        if not hasattr( top, "_tracing" ):
          top._tracing = PassMetadata()
        top._tracing.collect_text_sigs = self.collect_sig_func( top, top._tracing )

  def collect_sig_func( self, top, wavmeta ):

    # TODO use actual nets to reduce the amount of saved signals

    # Give all ' and " characters a preceding backslash for .format
    wav_srcs = []

    # Now we create per-cycle signal value collect functions
    for x in top._dsl.all_signals:
      if x.is_top_level_signal() and ( not repr(x).endswith('.clk') or x is top.clk ):
        if is_bitstruct_class( x._dsl.Type ):
          wav_srcs.append( "wavmeta.text_sigs['{0}'].append( to_bits({0}).bin() )".format(x) )
        elif issubclass( x._dsl.Type, Bits ):
          wav_srcs.append( "wavmeta.text_sigs['{0}'].append( {0}.bin() )".format(x) )

    wavmeta.text_sigs = defaultdict(list)

    # TODO use integer index instead of dict, should be easy
    src =  """
def dump_wav():
  {}
""".format( "\n  ".join(wav_srcs) )
    s, l_dict = top, {}
    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)
    return l_dict['dump_wav']
