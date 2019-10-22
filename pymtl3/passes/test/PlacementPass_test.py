"""
#=========================================================================
# PlacementPass_test.py
#=========================================================================
# Test for placement pass.
#
# Author : Cheng Tan
#   Date : Oct 22, 2019
"""
from pymtl3                           import *
from pymtl3.passes.PlacementPass      import PlacementPass

class Room( Component ):
  

class House( Component ):

  def construct( s, room_count ):
    s.room_count = room_count
    s.routers = [ Room() for _ in range( room_count ) ]

  def physical_elaborate( s ):
    s.dim_x

