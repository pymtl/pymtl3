"""
========================================================================
UnrollTickPass.py
========================================================================
Generate an unrolled tick function

Author : Shunning Jiang
Date   : Dec 26, 2018
"""


from __future__ import absolute_import, division, print_function

import py

from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError


class UnrollTickPass( BasePass ):

  def __call__( self, top ):
    if not hasattr( top._sched, "schedule" ):
      raise PassOrderError( "schedule" )

    schedule = top._sched.schedule

    # Berkin IlBeyi's recipe
    strs = map( "  update_blk{}() # {}".format, xrange( len(schedule) ), \
                                              [ x.__name__ for x in schedule ] )
    gen_tick_src = """
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}""".format( "; ".join( map(
                        "update_blk{0} = schedule[{0}]".format,
                        xrange( len( schedule ) ) ) ),
                        "\n          ".join( strs ) )

    exec(py.code.Source( gen_tick_src ).compile(), locals())

    top.tick = tick_unroll
