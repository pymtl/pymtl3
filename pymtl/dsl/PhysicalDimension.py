#=========================================================================
# PhysicalDimension.py
#=========================================================================
# Dimension information for each module
#
# Author : Cheng Tan
#   Date : May 7, 2019

#-------------------------------------------------------------------------
# Dimension information used for floorplanning and topology demo 
#-------------------------------------------------------------------------

class PhysicalDimension( object ):

  def __init__( s ):
    s.x     = 0
    s.y     = 0
    s.w     = 0
    s.h     = 0

  def __str__( s ):
    return "({},{}|{},{}|{},{})".format( s.x, s.y, s.w, s.h, 
            s.x + s.w, s.y + s.h )
