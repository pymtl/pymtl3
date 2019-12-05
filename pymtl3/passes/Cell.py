"""
#=========================================================================
# Cell.py
#=========================================================================
# everything in the same granularity should have the same height
# but probably different width (that will be aligned as much as
# possible).
#
# Author : Cheng Tan
#   Date : Oct 28, 2019
"""

class Cell( object ):
  def __init__( s, row_id = 0, col_id = 0, rows = 1, cols = 1 ):
    s.sub_cells = None
    s.parent = None
    s.row_id = row_id
    s.col_id = col_id
    s.component = None
    s.x_ratio = 0.0
    s.y_ratio = 0.0
    s.w_ratio = 1.0
    s.h_ratio = 1.0
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 0
    s.dim_h = 0
    s.isLeaf = False
    s.rows = 0
    s.cols = 0

  def bond( s, components ):
    if type(components) != list:
      s.setComponent( comonents )
    else:
      s.sub_cells = s.divide( 1, len(components) )
      for i in range( len(components) ):
        s.sub_cells[0][i].setComponent( components[i] )

  def divide( s, rows, cols ):
    s.rows = rows
    s.cols = cols
    s.sub_cells = [ [ Cell(i,j) for j in range(cols) ]
                      for i in range(rows) ]
    w_ratio = s.w_ratio/cols
    h_ratio = s.h_ratio/rows
    for r in range( rows ):
      for c in range( cols ):
        s.sub_cells[r][c].w_ratio = w_ratio
        s.sub_cells[r][c].h_ratio = h_ratio
        s.sub_cells[r][c].x_ratio = s.x_ratio + c*w_ratio
        s.sub_cells[r][c].y_ratio = s.y_ratio + r*h_ratio
        s.sub_cells[r][c].parent = s
    return s.sub_cells

  def updateParentDim( s, child_dim_w, child_dim_h ):
    if s.dim_w < child_dim_w * s.cols:
      s.dim_w = child_dim_w * s.cols
      if hasattr( s.component, "dim_w" ):
        if s.component.dim_w == 0:
          s.component.dim_w = s.dim_w
    if s.dim_h < child_dim_h * s.rows:
      s.dim_h = child_dim_h * s.rows
      if hasattr( s.component, "dim_h" ):
        if s.component.dim_h == 0:
          s.component.dim_h = s.dim_h
#    max_dim_w = s.sub_cells[0][0].dim_w
#    max_dim_h = s.sub_cells[0][0].dim_h
#    for i in range( s.rows ):
#      for j in range( s.cols ):
#        if s.sub_cells[i][j].dim_w > max_dim_w:
#          max_dim_w = s.sub_cells[i][j].dim_w
#        elif s.sub_cells[i][j].dim_h > max_dim_h:
#          max_dim_h = s.sub_cells[i][j].dim_h
#    for i in range( s.rows ):
#      for j in range( s.cols ):
#        s.sub_cells[i][j].dim_w = max_dim_w
#        s.sub_cells[i][j].dim_h = max_dim_h

  def updateChildrenDim( s ):
    if s.sub_cells == None:
      return
    for i in range( s.rows ):
      for j in range( s.cols ):
        s.sub_cells[i][j].dim_x = j * s.dim_w * s.sub_cells[i][j].w_ratio
        s.sub_cells[i][j].dim_y = i * s.dim_w * s.sub_cells[i][j].w_ratio
        if s.sub_cells[i][j].component != None:
          s.sub_cells[i][j].component.dim_x = s.sub_cells[i][j].dim_x
          s.sub_cells[i][j].component.dim_y = s.sub_cells[i][j].dim_y
        s.sub_cells[i][j].dim_w = s.dim_w * s.sub_cells[i][j].w_ratio
        s.sub_cells[i][j].dim_h = s.dim_h * s.sub_cells[i][j].h_ratio
        s.sub_cells[i][j].updateChildrenDim()

  def setComponent( s, component ):
    s.component = component
    print( "now in ", component._dsl.my_name )
    if hasattr( component, "sub_cells" ):
      print( "there is sub_cells..." )
    else:
      print( "no sub_cells..." )
    s.dim_w = component.dim_w
    s.dim_h = component.dim_h

