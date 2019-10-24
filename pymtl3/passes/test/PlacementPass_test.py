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

class Room( Component ):

  def construct( s, room_id ):
    s.room_id = room_id

  def place( s ):
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 10
    s.dim_h = 10

class House( Component ):

  def construct( s, room_count ):
    s.room_count = room_count
    s.rooms = [ Room( room_id ) for room_id in range( room_count ) ]

  def place( s ):
    BOUNDARY = 10
    INTERVAL = 50

    s.dim_w = BOUNDARY - INTERVAL
    s.dim_h = BOUNDARY - INTERVAL
    for room in s.rooms:
      s.dim_w += INTERVAL + room.dim_w
      s.dim_h += INTERVAL + room.dim_h
      room.dim_x = s.dim_w - room.dim_w
      room.dim_y = s.dim_h - room.dim_h

    s.dim_w += BOUNDARY
    s.dim_h += BOUNDARY

def test_place():
  model = House( 5 )
  model.elaborate()
  model.apply( PlacementPass() )

  # Generate the floorplanning script

  print( '\n---- placement geometric information ----' )
  print( "createFence top {} {} {} {}\n".format( model.dim_x, model.dim_y,
      model.dim_x + model.dim_w, model.dim_y + model.dim_h ) )
  for i, r in enumerate( model.rooms ):
    print( "createFence submodel__{} {} {} {} {}".format( str(i),
        r.dim_x, r.dim_y, r.dim_x + r.dim_w, r.dim_y + r.dim_h ) )

  print( '---------------------' )

