"""
========================================================================
WrapGreenletPass.py
========================================================================
Wrap all update blocks that call methods with blocking decorator with
greenlet.

Author : Shunning Jiang
Date   : May 20, 2019
"""
from greenlet import greenlet

from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class WrapGreenletPass( BasePass ):
  def __call__( self, top ):
    if not hasattr( top, "_dag" ):
      raise PassOrderError( "_dag" )

    self.wrap_greenlet( top )

  def wrap_greenlet( self, top ):

    all_upblks      = top._dag.final_upblks
    all_constraints = top._dag.all_constraints
    greenlet_upblks = top._dag.greenlet_upblks

    top._dag.blk_greenlet_mapping = blk_greenlet_mapping = {}

    if not greenlet_upblks:
      return

    def wrap_greenlet( blk ):

      def greenlet_wrapper():
        while True:
          blk()
          greenlet.getcurrent().parent.switch()

      gl = greenlet( greenlet_wrapper )

      def greenlet_ticker():
        gl.switch()

      # greenlet_ticker.greenlet = gl
      greenlet_ticker.__name__ = blk.__name__

      return greenlet_ticker

    new_upblks  = set()

    for blk in all_upblks:
      if blk in greenlet_upblks:
        wrapped = wrap_greenlet( blk )
        blk_greenlet_mapping[ blk ] = wrapped
        new_upblks.add( wrapped )
      else:
        new_upblks.add( blk )

    new_constraints = set()

    for (x, y) in all_constraints:
      if x in greenlet_upblks:
        x = blk_greenlet_mapping[ x ]
      if y in greenlet_upblks:
        y = blk_greenlet_mapping[ y ]

      new_constraints.add( (x, y) )

    top._dag.final_upblks    = new_upblks
    top._dag.all_constraints = new_constraints
    top._dag.blk_greenlet_mapping = blk_greenlet_mapping
