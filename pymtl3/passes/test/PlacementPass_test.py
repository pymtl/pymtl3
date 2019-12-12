"""
#=========================================================================
# PlacementPass_test.py
#=========================================================================
# Test for placement pass.
#
# Author : Cheng Tan
#   Date : Oct 22, 2019
"""
from pymtl3                      import *
from pymtl3.passes.PlacementPass import PlacementPass
from pymtl3.passes.Cell          import Cell

class Wall( Component ):
  def construct( s, wall_id ):
    s.wall_id = wall_id

  def place( s, width = 40, height = 20 ):
    # assume this is the most fine-granularity component
    s.dim_w = width
    s.dim_h = height

class SmallRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, width = 10, height = 10 ):
    # assume this is the most fine-granularity component
    s.dim_w = width
    s.dim_h = height

class BigRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, width = 20, height = 20 ):
    # assume this is the most fine-granularity component
    s.dim_w = width
    s.dim_h = height

class House( Component ):
  def construct( s, big_room_count, wall_count, small_room_count):
    s.big_room_count   = big_room_count
    s.wall_count       = wall_count
    s.small_room_count = small_room_count

    s.big_rooms   = [ BigRoom  ( i ) for i in range( big_room_count   ) ]
    s.walls       = [ Wall     ( i ) for i in range( wall_count       ) ]
    s.small_rooms = [ SmallRoom( i ) for i in range( small_room_count ) ]

  def place( s, width = 100, height = 0 ):

    # should feed the width and height to the internal dim_w and dim_h.
    s.dim_w = width
    s.dim_h = height

    # should always split cell into boxes to place sub-components.
    # otherwise, the sub-components will be recognized as a black box.
    s.sub_cells = s.cell.split( rows = 3, cols = 1 )
    s.sub_cells[0][0].bond( s.big_rooms   )
    s.sub_cells[1][0].bond( s.walls       )
    s.sub_cells[2][0].bond( s.small_rooms )

#-------------------------------------------------------------------------
# test placement pass with detailed outputs
#-------------------------------------------------------------------------

def test_place():

  model = House( 4, 1, 4 )
  model.elaborate()
  model.apply( PlacementPass() )

  # Generate the floorplanning script
  print( "\n---- placement geometric information ----" )
  print( "============ cell ratio ==============" )
  for j in range( model.big_room_count ):
    print( "[cell] big room x_ratio[", j, "]: ", model.cell.sub_cells[0][0].sub_cells[0][j].x_ratio )
    print( "[cell] big room y_ratio[", j, "]: ", model.cell.sub_cells[0][0].sub_cells[0][j].y_ratio )
    print( "[cell] big room w_ratio[", j, "]: ", model.cell.sub_cells[0][0].sub_cells[0][j].w_ratio )
    print( "[cell] big room h_ratio[", j, "]: ", model.cell.sub_cells[0][0].sub_cells[0][j].h_ratio )
    print( "--------------------------" )

  for j in range( model.wall_count ):
    print( "[cell] wall x_ratio[", j, "]: ", model.cell.sub_cells[1][0].sub_cells[0][j].x_ratio )
    print( "[cell] wall y_ratio[", j, "]: ", model.cell.sub_cells[1][0].sub_cells[0][j].y_ratio )
    print( "[cell] wall w_ratio[", j, "]: ", model.cell.sub_cells[1][0].sub_cells[0][j].w_ratio )
    print( "[cell] wall h_ratio[", j, "]: ", model.cell.sub_cells[1][0].sub_cells[0][j].h_ratio )

  print( "--------------------------" )

  for j in range( model.small_room_count ):
    print( "[cell] small room x_ratio[", j, "]: ", model.cell.sub_cells[2][0].sub_cells[0][j].x_ratio )
    print( "[cell] small room y_ratio[", j, "]: ", model.cell.sub_cells[2][0].sub_cells[0][j].y_ratio )
    print( "[cell] small room w_ratio[", j, "]: ", model.cell.sub_cells[2][0].sub_cells[0][j].w_ratio )
    print( "[cell] small room h_ratio[", j, "]: ", model.cell.sub_cells[2][0].sub_cells[0][j].h_ratio )
    print( "--------------------------" )

  print( "============ component dim ==============" )
  for j in range( model.big_room_count ):
    print( "[dim] big room x[", j, "]: ", model.big_rooms[j].dim_x )
    print( "[dim] big room y[", j, "]: ", model.big_rooms[j].dim_y )
    print( "[dim] big room w[", j, "]: ", model.big_rooms[j].dim_w )
    print( "[dim] big room h[", j, "]: ", model.big_rooms[j].dim_h )
    print( "--------------------------" )

  for j in range( model.wall_count ):
    print( "[dim] wall x[", j, "]: ", model.walls[j].dim_x )
    print( "[dim] wall y[", j, "]: ", model.walls[j].dim_y )
    print( "[dim] wall w[", j, "]: ", model.walls[j].dim_w )
    print( "[dim] wall h[", j, "]: ", model.walls[j].dim_h )

  print( "--------------------------" )

  for j in range( model.small_room_count ):
    print( "[dim] small room x[", j, "]: ", model.small_rooms[j].dim_x )
    print( "[dim] small room y[", j, "]: ", model.small_rooms[j].dim_y )
    print( "[dim] small room w[", j, "]: ", model.small_rooms[j].dim_w )
    print( "[dim] small room h[", j, "]: ", model.small_rooms[j].dim_h )
    print( "--------------------------" )

  print( "============= top =============" )
  print( "[top] house cell x: ", model.cell.dim_x )
  print( "[top] house cell y: ", model.cell.dim_y )
  print( "[top] house cell w: ", model.cell.dim_w )
  print( "[top] house cell h: ", model.cell.dim_h )
  print( "--------------------------" )
  print( "[dim] house dim x: ", model.dim_x )
  print( "[dim] house dim y: ", model.dim_y )
  print( "[dim] house dim w: ", model.dim_w )
  print( "[dim] house dim h: ", model.dim_h )
  print( "--------------------------" )

