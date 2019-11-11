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

from pymtl3.datatypes import is_bitstruct_class
from pymtl3.dsl import Const
from pymtl3.passes.BasePass import BasePass, PassMetadata

from ..errors import ModelTypeError, PassOrderError


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

    # TODO use actual nets to reduce the amount of saved signals

    # Give all ' and " characters a preceding backslash for .format
    wav_srcs = []

    # Now we create per-cycle signal value collect functions
    for x in top._dsl.all_signals:
      if x.is_top_level_signal() and ( not repr(x).endswith('.clk') or x is top.clk ):
        if is_bitstruct_class( x._dsl.Type ):
          raise ModelTypeError("designs without Bitstruct signals.\n"
                               "- Currently text waveform cannot dump design with bitstruct.\n"
                               "- :) The bitstruct is usually too wide to display anyways.")
        wav_srcs.append( "wavmeta.sigs['{0}'].append( {0}.bin() )".format(x) )

    wavmeta.sigs = defaultdict(list)

    # TODO use integer index instead of dict, should be easy
    src =  """
def dump_wav():
  {}
""".format( "\n  ".join(wav_srcs) )
    s, l_dict = top, {}
    exec(compile( src, filename="temp", mode="exec"), globals().update(locals()), l_dict)
    return l_dict['dump_wav']
