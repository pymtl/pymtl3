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
  def __init__( s, row_id = 0, col_id = 0, rows = 1, cols = 1,
                component = None ):
    s.sub_cells = None
    s.parent = None
    s.row_id = row_id
    s.col_id = col_id
    s.component = component
    s.x_ratio = 0.0
    s.y_ratio = 0.0
    s.w_ratio = 1.0
    s.h_ratio = 1.0
    s.dim_x = 0
    s.dim_y = 0
    s.dim_w = 0
    s.dim_h = 0
    s.rows = 0
    s.cols = 0

  #-----------------------------------------------------------------------
  # bond specific component with cell
  #-----------------------------------------------------------------------

  def bond( s, components ):

    if type(components) != list:
      s.component = components
      # update the width and height of the cell
      if s.dim_w < components.dim_w:
       s.dim_w = components.dim_w
      if s.dim_h < components.dim_h:
        s.dim_h = components.dim_h
    else:
      # by default, we automatically split the cell in horizontal
      s.sub_cells = s.split( 1, len(components) )
      for i in range( len(components) ):
        s.sub_cells[0][i].component = components[i]
        # update the width and height of the cell
        if s.sub_cells[0][i].dim_w < components[i].dim_w:
         s.sub_cells[0][i].dim_w = components[i].dim_w
        if s.sub_cells[0][i].dim_h < components[i].dim_h:
          s.sub_cells[0][i].dim_h = components[i].dim_h


  #-----------------------------------------------------------------------
  # split the cell into sub-cells
  #-----------------------------------------------------------------------

  def split( s, rows, cols ):
    s.rows = rows
    s.cols = cols
    s.sub_cells = [[ Cell(i,j) for j in range(cols) ]
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

  #-----------------------------------------------------------------------
  # hierarchically (upwards/downwards) update the
  # dimension information of cells and components.
  #-----------------------------------------------------------------------

  def update_dim_info( s ):
    s.update_size_upwards()
    s.update_size_downwards()

  #-----------------------------------------------------------------------
  # update the dimension information of the parent cell
  #-----------------------------------------------------------------------

  def update_parent( s ):
    if s.parent.dim_w < s.dim_w * s.parent.cols:
      s.parent.dim_w = s.dim_w * s.parent.cols
      if hasattr( s.parent.component, "dim_w" ):
        if s.parent.component.dim_w == 0:
          s.parent.component.dim_w = s.parent.dim_w
    if s.parent.dim_h < s.dim_h * s.parent.rows:
      s.parent.dim_h = s.dim_h * s.parent.rows
      if hasattr( s.parent.component, "dim_h" ):
        if s.parent.component.dim_h == 0:
          s.parent.component.dim_h = s.parent.dim_h

  #-----------------------------------------------------------------------
  # hierarchically update the cell's dimension information
  # from bottom to top
  #-----------------------------------------------------------------------

  def update_size_upwards( s ):
    if s.component != None:
      s.bond( s.component )
    if s.sub_cells == None:
      return
    for r in range( len( s.sub_cells ) ):
      for c in range( len( s.sub_cells[r] ) ):
        s.sub_cells[r][c].update_size_upwards()
        s.sub_cells[r][c].update_parent()


  #-----------------------------------------------------------------------
  # hierarchically update the cell's size and the component's coordinate
  # information from top to bottom
  #-----------------------------------------------------------------------

  def update_size_downwards( s ):
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
        s.sub_cells[i][j].update_size_downwards()

