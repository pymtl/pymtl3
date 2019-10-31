#=========================================================================
# PlacementPass.py
#=========================================================================
# Generate placement geometric information module recursively.
#
# Author : Cheng Tan
# Date   : Oct 22, 2019

from pymtl3.passes.BasePass import BasePass
from collections            import deque
from pymtl3.passes.Grid     import Grid

def calculateDFS( grid ):
  for r in range( len( grid.sub_grids ) ):
    for c in range( len( grid.sub_grids[r] ) ):
      if not grid.sub_grids[r][c].isLeaf:
        calculateDFS( grid.sub_grids[r][c] )
      grid.sub_grids[r][c].parent.updateChildDim(
          grid.sub_grids[r][c].dim_w,
          grid.sub_grids[r][c].dim_h )

class PlacementPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "place" ):
      print( "Note that there is no place defined in "
             "module:{}".format(top.__class__.__name__) )
      return

    all_components = sorted( top.get_all_components(), key=repr )
#    all_components.reverse()
#    for c in all_components:
#      if hasattr( c, "place" ):
#        c.place()
    top_grid  = Grid( row_id=0, col_id=0 )
    top.place( top_grid )

    calculateDFS( top_grid )

    print( "============= top =============" )
    print( "[top] house x: ", top_grid.dim_x )
    print( "[top] house y: ", top_grid.dim_y )
    print( "[top] house w: ", top_grid.dim_w )
    print( "[top] house h: ", top_grid.dim_h )

