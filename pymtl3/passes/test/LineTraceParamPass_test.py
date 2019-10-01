"""
#=========================================================================
# LineTraceParamPass_test.py
#=========================================================================
# Test for multi-level line trace pass.
#
# Author : Yanghui Ou
#   Date : 29 May, 2019
"""
from pymtl3.dsl import *
from pymtl3.passes.CLLineTracePass import CLLineTracePass
from pymtl3.passes.GenDAGPass import GenDAGPass
from pymtl3.passes.LineTraceParamPass import LineTraceParamPass
from pymtl3.passes.SimpleSchedulePass import SimpleSchedulePass
from pymtl3.passes.SimpleTickPass import SimpleTickPass
from pymtl3.passes.WrapGreenletPass import WrapGreenletPass


def test_multi_level_trace():

  class Top( Component ):
    def construct( s ):
      s.simple_trace = 'simple'
      s.verbose_trace = 'verbose'

    def line_trace( s, level='simple' ):
      if level == 'simple':
        return f"{s.simple_trace}"
      elif level == 'verbose':
        return f"{s.verbose_trace}"
      else:
        return "default"

  A = Top()
  A.set_param( 'top.line_trace', level='verbose' )
  A.elaborate()
  A.apply( GenDAGPass()              )
  A.apply( WrapGreenletPass()        )
  A.apply( SimpleSchedulePass()      )
  A.apply( CLLineTracePass()         )
  A.apply( SimpleTickPass()          )
  A.apply( LineTraceParamPass()      )
  A.lock_in_simulation()
  A.tick()
  print( A.line_trace() )
  assert A.line_trace() == "verbose"
