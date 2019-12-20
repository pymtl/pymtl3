#=========================================================================
# transpose.py
#=========================================================================
# Author: Shunning Jiang
# Date  : Dec 19, 2019


class Transpose( Component ):
  """ bsg_transpose

  https://github.com/bespoke-silicon-group/basejump_stl/blob/master/bsg_misc/bsg_transpose.v

  Args:
    width (int): X-dim width of input / Y-dim width of output
    els (int): Y-dim width of input / X-dim width of output

  Variables:
    i: els-element width-bit input port array
    o: width-element els-bit output port array
  """

  def construct( s, width, els ):
    s.i = [ InPort( mk_bits(width) ) for _ in range(els) ]
    s.o = [ OutPort( mk_bits(els) ) for _ in range(width) ]

    for x in range(width):
      for y in range(els):
        o[y][x] //= i[x][y]

  def line_trace( s ):
    return ""
