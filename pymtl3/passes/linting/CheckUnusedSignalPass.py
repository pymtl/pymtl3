"""
========================================================================
CheckUnusedSignalPass.py
========================================================================

Author : Shunning Jiang
Date   : Dec 29, 2019
"""

from pymtl3.dsl import MetadataKey
from pymtl3.passes.BasePass import BasePass


class CheckUnusedSignalPass( BasePass ):

  result = MetadataKey(list)

  def __call__( self, top ):
    used_signals = set()
    # check all components and connectables
    for writer, net in top.get_all_value_nets():
      for x in net:
        used_signals.add( x.get_top_level_signal() )

    upblk_reads, upblk_writes, _ = top.get_all_upblk_metadata()
    for blk, reads in upblk_reads.items():
      for rd in reads:
        used_signals.add( rd.get_top_level_signal() )

    for blk, writes in upblk_writes.items():
      for wr in writes:
        used_signals.add( wr.get_top_level_signal() )

    unused = sorted( top.get_all_signals() - used_signals, key=repr )

    top.set_metadata( self.result, unused )
    print("\n[CheckUnusedSignalPass] These signals are NEVER used and can be removed from source code: \n  - ",end="")
    print("\n  - ".join( [ f"{x!r} of class {x.__class__.__name__}" for x in unused ] ) )
