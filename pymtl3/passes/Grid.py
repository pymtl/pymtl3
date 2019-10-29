"""
#=========================================================================
# Grid.py
#=========================================================================
# everything in the same granularity should have the same height
# but probably different width (that will be aligned as much as
# possible).
#
# Author : Cheng Tan
#   Date : Oct 28, 2019
"""

class Grid( object ):
  def __init__( s, row_id, col_id, parent=None ):
    s.sub_grids = None
    s.parent = parent
    s.row_id = row_id
    s.col_id = col_id
    s.component = None

  def divide( s, rows, cols ):
    s.sub_grids = [ [ Grid(i,j,s) for j in range(cols) ]
                      for i in range(rows) ]
    return s.sub_grids

  def setComponent( s, component ):
    s.component = component

