"""
========================================================================
SimpleTickPass.py
========================================================================
Generate a simple tick function (no Mamba techniques here)

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass

from .errors import PassOrderError


class SimpleTickPass( BasePass ):

  @staticmethod
  def gen_tick_function( schedule ):
    def iterative():
      for blk in schedule:
        blk()
    return iterative

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule


    top.tick = SimpleTickPass.gen_tick_function( schedule )
