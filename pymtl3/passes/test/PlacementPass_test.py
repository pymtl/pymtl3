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
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 40
    s.dim_h = 40
    grid.setComponent( s )

class SmallRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, grid ):
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 10
    s.dim_h = 10
    grid.setComponent( s )

class BigRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, grid ):
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
    sub_grids = grid.divide( rows = 3, cols = 1 )

    big_room_grids   = sub_grids[0][0].divide( rows=1,
                       cols=s.big_room_count )
    small_room_grids = sub_grids[2][0].divide( rows=1,
                       cols=s.small_room_count )

    for i in range( s.big_room_count ):
      s.big_rooms[i].place( big_room_grids[0][i] )

    s.walls[0].place( sub_grids[1][0] )

    for j in range( s.small_room_count ):
      s.small_rooms[j].place( small_room_grids[0][j] )

    grid.setComponent( s )
    
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

