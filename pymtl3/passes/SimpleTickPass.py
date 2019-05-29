"""
========================================================================
SimpleTickPass.py
========================================================================
Generate a simple tick function (no Mamba techniques here)

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
from __future__ import absolute_import, division, print_function

from graphviz import Digraph

from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass

from .errors import PassOrderError


class SimpleTickPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule

    def tick_normal():
      for blk in schedule:
        blk()

    top.tick = tick_normal
