"""
========================================================================
RefactoringAnalysisPass.py
========================================================================

Author : Shunning Jiang
Date   : June 15, 2020
"""

from pymtl3 import *

from ..BasePass import BasePass


class RefactoringAnalysisPass( BasePass ):

  def __call__( self, top ):
    print("[RefactoringAnalysisPass] Making plots ...\n")
    self.plot_total_in_out_bw( top )
    self.plot_total_upblk_lines_histo( top )

  # Creating X-Y scatter plot where X axis is the total number of
  def plot_total_in_out_bw( self, top ):
    bw = []
    for c in top.get_all_object_filter( lambda x: isinstance( x, Component ) ):
      tot_in = tot_out = 0
      for inp in c.get_input_ports():
        tot_in += inp.get_type().nbits
      for out in c.get_output_ports():
        tot_out += out.get_type().nbits
      bw.append( (tot_in, tot_out, repr(c)) )

    import matplotlib.pyplot as plt
    plt.scatter( [ i for (i,o,n) in bw ], [ o for (i,o,n) in bw ],
                 s=[ 1.5 for _ in range(len(bw))])
    plt.xlabel( 'total input bitwidth' )
    plt.ylabel( 'total output bitwidth' )
    plt.savefig(f"{top.__class__.__name__}_inout_bw_scatter.pdf", format="pdf")
    plt.close()

  def plot_total_upblk_lines_histo( self, top ):
    histo = []

    for c in top.get_all_object_filter( lambda x: isinstance( x, Component ) ):
      for blk in c.get_update_blocks():
        is_lambda, src, _, _, _ = c.get_update_block_info( blk )
        lines = src.split('\n')

        if lines[-1] == '': lines.pop()

        if not is_lambda:
          assert lines[0].lstrip(" ").startswith("@update")
          assert lines[1].lstrip(" "),startswith("def ") and lines[1].endswith(":")
          histo.append( len(lines) - 2 )

        else:
          histo.append( len(lines) )

    import matplotlib.pyplot as plt
    plt.hist( histo, bins=range(max(histo)) )
    plt.xlabel( 'number of lines in update block' )
    plt.ylabel( 'update block count' )
    plt.savefig(f"{top.__class__.__name__}_histogram.pdf", format="pdf")
