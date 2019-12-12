#=========================================================================
# PlacementPass.py
#=========================================================================
# Generate placement geometric information module recursively.
#
# Author : Cheng Tan
# Date   : Oct 22, 2019

from pymtl3.passes.BasePass import BasePass
from collections            import deque
from pymtl3.passes.Cell     import *

class PlacementPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "place" ):
      print( "Note that there is no place defined in "
             "module:{}".format(top.__class__.__name__) )
      return

    all_components = sorted( top.get_all_components(), key=repr )
    all_components.reverse()
    top_cell = Cell( component = top )
    top.cell = top_cell
    for c in all_components:
      if hasattr( c, "place" ):
        # can also give customized width/height parameters
        # for specific component, for example:
        # fft_module.place(20, 30)
        c.place()

    top_cell.update_dim_info()

