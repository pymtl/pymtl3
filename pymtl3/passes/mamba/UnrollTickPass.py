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
    strs = [f"  update_blk{idx}() # {sched}" for idx, sched in \
        enumerate([ x.__name__ for x in schedule ])]

    gen_tick_src = """
        def compile_unroll( schedule ):
          {}
          def tick_unroll():
            # The code below does the actual calling of update blocks.
          {}
          return tick_unroll
        """.format( ";".join( map(
                        "update_blk{0}=schedule[{0}]".format,
                        range( len( schedule ) ) ) ),
                        "\n          ".join( strs ) )

    l = {}
    exec(py.code.Source( gen_tick_src ).compile(), l)
    return l['compile_unroll']( schedule )

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    if hasattr( top, "_cl_trace" ):
      schedule = top._cl_trace.schedule
    else:
      schedule = top._sched.schedule


    top.tick = UnrollTickPass.gen_tick_function( schedule )
