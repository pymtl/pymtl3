#=========================================================================
# SimpleTickPass.py
#=========================================================================
# Generate a simple tick function (no Mamba techniques here)
#
# Author : Shunning Jiang
# Date   : Dec 26, 2018

from collections      import deque
from graphviz         import Digraph

from pymtl.passes     import BasePass
from pymtl.dsl.errors import UpblkCyclicError

from errors           import PassOrderError

class SimpleTickPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    schedule = top._sched.schedule

    def tick_normal():
      for blk in schedule:
        blk()

    top.tick = tick_normal
