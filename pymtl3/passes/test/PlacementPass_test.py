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
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 40
    s.dim_h = 20

class SmallRoom( Component ):
  def construct( s, room_id ):
    s.room_id = room_id

  def place( s, width = 10, height = 10 ):
    # assume this is the most fine-granularity component
    s.dim_w = 10
    s.dim_h = 10

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
    s.dim_w = width
    s.dim_h = height

    s.sub_cells = s.cell.divide( rows = 3, cols = 1 )
    s.sub_cells[0][0].bond( s.big_rooms   )
    s.sub_cells[1][0].bond( s.walls       )
    s.sub_cells[2][0].bond( s.small_rooms )

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

