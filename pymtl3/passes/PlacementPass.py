#=========================================================================
# PlacementPass.py
#=========================================================================
# Generate placement geometric information module recursively.
#
# Author : Cheng Tan
# Date   : Oct 22, 2019

from pymtl3.passes.BasePass import BasePass
from collections            import deque
from pymtl3.passes.Cell     import Cell

def updateDim( cell ):
  if cell.sub_cells == None:
    return
  for r in range( len( cell.sub_cells ) ):
    for c in range( len( cell.sub_cells[r] ) ):
#      if not cell.sub_cells[r][c].isLeaf:
      updateDim( cell.sub_cells[r][c] )
      cell.sub_cells[r][c].parent.updateChildDim(
          cell.sub_cells[r][c].dim_w,
          cell.sub_cells[r][c].dim_h )

class PlacementPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top, "place" ):
      print( "Note that there is no place defined in "
             "module:{}".format(top.__class__.__name__) )
      return

    all_components = sorted( top.get_all_components(), key=repr )
    all_components.reverse()
    top_cell = Cell()
    top.cell = top_cell
    for c in all_components:
      if hasattr( c, "place" ):
        # can also give customized width/height parameters
        # for specific component
        c.place()
    top_cell.setComponent( top )

    updateDim( top_cell )

    print( "============= top =============" )
    print( "[top] house x: ", top_cell.dim_x )
    print( "[top] house y: ", top_cell.dim_y )
    print( "[top] house w: ", top_cell.dim_w )
    print( "[top] house h: ", top_cell.dim_h )

    print()
    print( "============ cell ratio ==============" )
    for j in range( top.big_room_count ):
      print( "[cell] big room x[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].x_ratio )
      print( "[cell] big room y[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].y_ratio )
      print( "[cell] big room w[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].w_ratio )
      print( "[cell] big room h[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].h_ratio )
      print( "--------------------------" )

    for j in range( top.wall_count ):
      print( "[cell] wall x[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].x_ratio )
      print( "[cell] wall y[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].y_ratio )
      print( "[cell] wall w[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].w_ratio )
      print( "[cell] wall h[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].h_ratio )

    print( "--------------------------" )

    for j in range( top.small_room_count ):
      print( "[cell] small room x[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].x_ratio )
      print( "[cell] small room y[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].y_ratio )
      print( "[cell] small room w[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].w_ratio )
      print( "[cell] small room h[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].h_ratio )
      print( "--------------------------" )

    print( "============ component dim ==============" )
    for j in range( top.big_room_count ):
      print( "[dim] big room x[", j, "]: ", top.big_rooms[j].dim_x )
      print( "[dim] big room y[", j, "]: ", top.big_rooms[j].dim_y )
      print( "[dim] big room w[", j, "]: ", top.big_rooms[j].dim_w )
      print( "[dim] big room h[", j, "]: ", top.big_rooms[j].dim_h )
      print( "--------------------------" )

    for j in range( top.wall_count ):
      print( "[dim] wall x[", j, "]: ", top.walls[j].dim_x )
      print( "[dim] wall y[", j, "]: ", top.walls[j].dim_y )
      print( "[dim] wall w[", j, "]: ", top.walls[j].dim_w )
      print( "[dim] wall h[", j, "]: ", top.walls[j].dim_h )

    print( "--------------------------" )

    for j in range( top.small_room_count ):
      print( "[dim] small room x[", j, "]: ", top.small_rooms[j].dim_x )
      print( "[dim] small room y[", j, "]: ", top.small_rooms[j].dim_y )
      print( "[dim] small room w[", j, "]: ", top.small_rooms[j].dim_w )
      print( "[dim] small room h[", j, "]: ", top.small_rooms[j].dim_h )
      print( "--------------------------" )


