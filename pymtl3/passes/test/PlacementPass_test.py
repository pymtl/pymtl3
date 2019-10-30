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
from pymtl3.passes.Grid          import Grid

class Wall( Component ):
  def construct( s, wall_id ):
    s.wall_id = wall_id

  def place( s, grid ):
    # assume this is the most fine-granularity component
    s.component_name = "wall"
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 40
    s.dim_h = 20
    grid.setComponent( s )

class SmallRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, grid ):
    # assume this is the most fine-granularity component
    s.component_name = "small room"
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 10
    s.dim_h = 10
    grid.setComponent( s )

class BigRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, grid ):
    # assume this is the most fine-granularity component
    s.component_name = "big room"
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 20
    s.dim_h = 20
    grid.setComponent( s )

class House( Component ):
  def construct( s, big_room_count, wall_count, small_room_count):
    s.big_room_count = big_room_count
    s.wall_count = wall_count
    s.small_room_count = small_room_count
    s.big_rooms   = [ BigRoom( i )   for i in range( big_room_count ) ]
    s.walls       = [ Wall( i )      for i in range( wall_count ) ]
    s.small_rooms = [ SmallRoom( i ) for i in range( small_room_count ) ]

  def place( s, grid ):
    s.component_name = "house"
    s.sub_grids = grid.divide( rows = 3, cols = 1 )

    big_room_grids   = s.sub_grids[0][0].divide( rows = 1,
                       cols = s.big_room_count )
    wall_grids       = s.sub_grids[1]
    small_room_grids = s.sub_grids[2][0].divide( rows = 1,
                       cols = s.small_room_count )

    for i in range( s.big_room_count ):
      s.big_rooms[i].place( big_room_grids[0][i] )

    s.walls[0].place( wall_grids[0] )

    for i in range( s.small_room_count ):
      s.small_rooms[i].place( small_room_grids[0][i] )

    print()
    print( "============ grid ratio ==============" )
    for j in range( s.big_room_count ):
      print( "[grid] big room x[", j, "]: ", big_room_grids[0][j].x_ratio )
      print( "[grid] big room y[", j, "]: ", big_room_grids[0][j].y_ratio )
      print( "[grid] big room w[", j, "]: ", big_room_grids[0][j].w_ratio )
      print( "[grid] big room h[", j, "]: ", big_room_grids[0][j].h_ratio )
      print( "--------------------------" )

    for j in range( s.wall_count ):
      print( "[grid] wall x[", j, "]: ", wall_grids[j].x_ratio )
      print( "[grid] wall y[", j, "]: ", wall_grids[j].y_ratio )
      print( "[grid] wall w[", j, "]: ", wall_grids[j].w_ratio )
      print( "[grid] wall h[", j, "]: ", wall_grids[j].h_ratio )

    print( "--------------------------" )

    for j in range( s.small_room_count ):
      print( "[grid] small room x[", j, "]: ", small_room_grids[0][j].x_ratio )
      print( "[grid] small room y[", j, "]: ", small_room_grids[0][j].y_ratio )
      print( "[grid] small room w[", j, "]: ", small_room_grids[0][j].w_ratio )
      print( "[grid] small room h[", j, "]: ", small_room_grids[0][j].h_ratio )
      print( "--------------------------" )

    print( "============ component dim ==============" )
    for j in range( s.big_room_count ):
      print( "[dim] big room x[", j, "]: ", s.big_rooms[j].dim_x )
      print( "[dim] big room y[", j, "]: ", s.big_rooms[j].dim_y )
      print( "[dim] big room w[", j, "]: ", s.big_rooms[j].dim_w )
      print( "[dim] big room h[", j, "]: ", s.big_rooms[j].dim_h )
      print( "--------------------------" )

    for j in range( s.wall_count ):
      print( "[dim] wall x[", j, "]: ", s.walls[j].dim_x )
      print( "[dim] wall y[", j, "]: ", s.walls[j].dim_y )
      print( "[dim] wall w[", j, "]: ", s.walls[j].dim_w )
      print( "[dim] wall h[", j, "]: ", s.walls[j].dim_h )

    print( "--------------------------" )

    for j in range( s.small_room_count ):
      print( "[dim] small room x[", j, "]: ", s.small_rooms[j].dim_x )
      print( "[dim] small room y[", j, "]: ", s.small_rooms[j].dim_y )
      print( "[dim] small room w[", j, "]: ", s.small_rooms[j].dim_w )
      print( "[dim] small room h[", j, "]: ", s.small_rooms[j].dim_h )
      print( "--------------------------" )

    grid.setComponent( s )

    print( "============= top =============" )
    print( "[top] house x: ", grid.dim_x )
    print( "[top] house y: ", grid.dim_y )
    print( "[top] house w: ", grid.dim_w )
    print( "[top] house h: ", grid.dim_h )

def test_place():
  model = House( 4, 1, 4 )
  model.elaborate()
  model.apply( PlacementPass() )
  # Generate the floorplanning script
  print( "\n---- placement geometric information ----" )
  print( "createFence top {} {} {} {}\n".format( model.dim_x, model.dim_y,
         model.dim_x + model.dim_w, model.dim_y + model.dim_h ) )
  for i, r in enumerate( model.big_rooms ):
    print( "createFence submodel__{} {} {} {} {}".format( str(i),
           r.dim_x, r.dim_y, r.dim_x + r.dim_w, r.dim_y + r.dim_h ) )
  print( "---------------------" )

