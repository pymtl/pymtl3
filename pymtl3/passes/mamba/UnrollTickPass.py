"""
========================================================================
UnrollTickPass.py
========================================================================
Generate an unrolled tick function

Author : Shunning Jiang
Date   : Dec 26, 2018
"""

import py

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class UnrollTickPass( BasePass ):

  @staticmethod
  def gen_tick_function( schedule ):

    # Berkin IlBeyi's recipe ( updated using f-strings and enumerate )
    strs = [f"f{idx}() # {sched}" for idx, sched in \
        enumerate([ x.__name__ for x in schedule ])]

    gen_tick_src = """
      def tick_unroll():
        # The code below does the actual calling of update blocks.
        {}
      """.format( "\n        ".join( strs ) )

    from __pypy__ import newdict
    _globals = newdict("module")
    for i, x in enumerate(schedule):
      _globals[f"f{i}"] = x

    _locals  = newdict("module")
    exec(py.code.Source( gen_tick_src ).compile(), _globals, _locals)
    return _locals['tick_unroll']

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule


    top.tick = UnrollTickPass.gen_tick_function( schedule )
