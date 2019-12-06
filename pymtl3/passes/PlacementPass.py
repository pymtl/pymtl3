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
        # for specific component
        c.place()

    updateDim( top_cell )

    print()
    print( "============ cell ratio ==============" )
    for j in range( top.big_room_count ):
      print( "[cell] big room x_ratio[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].x_ratio )
      print( "[cell] big room y_ratio[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].y_ratio )
      print( "[cell] big room w_ratio[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].w_ratio )
      print( "[cell] big room h_ratio[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].h_ratio )
      print( "--------------------------" )

    for j in range( top.wall_count ):
      print( "[cell] wall x_ratio[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].x_ratio )
      print( "[cell] wall y_ratio[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].y_ratio )
      print( "[cell] wall w_ratio[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].w_ratio )
      print( "[cell] wall h_ratio[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].h_ratio )

    print( "--------------------------" )

    for j in range( top.small_room_count ):
      print( "[cell] small room x_ratio[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].x_ratio )
      print( "[cell] small room y_ratio[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].y_ratio )
      print( "[cell] small room w_ratio[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].w_ratio )
      print( "[cell] small room h_ratio[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].h_ratio )
      print( "--------------------------" )

    print( "============ cell dim ==============" )
    for j in range( top.big_room_count ):
      print( "[cell] big room x[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].dim_x )
      print( "[cell] big room y[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].dim_y )
      print( "[cell] big room w[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].dim_w )
      print( "[cell] big room h[", j, "]: ", top_cell.sub_cells[0][0].sub_cells[0][j].dim_h )
      print( "--------------------------" )

    for j in range( top.wall_count ):
      print( "[cell] wall x[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].dim_x )
      print( "[cell] wall y[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].dim_y )
      print( "[cell] wall w[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].dim_w )
      print( "[cell] wall h[", j, "]: ", top_cell.sub_cells[1][0].sub_cells[0][j].dim_h )

    print( "--------------------------" )

    for j in range( top.small_room_count ):
      print( "[cell] small room x[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].dim_x )
      print( "[cell] small room y[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].dim_y )
      print( "[cell] small room w[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].dim_w )
      print( "[cell] small room h[", j, "]: ", top_cell.sub_cells[2][0].sub_cells[0][j].dim_h )
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

    print( "============= top =============" )
    print( "[top] house cell x: ", top_cell.dim_x )
    print( "[top] house cell y: ", top_cell.dim_y )
    print( "[top] house cell w: ", top_cell.dim_w )
    print( "[top] house cell h: ", top_cell.dim_h )
    print( "--------------------------" )

    print( "[dim] house dim x[", j, "]: ", top.dim_x )
    print( "[dim] house dim y[", j, "]: ", top.dim_y )
    print( "[dim] house dim w[", j, "]: ", top.dim_w )
    print( "[dim] house dim h[", j, "]: ", top.dim_h )
    print( "--------------------------" )



