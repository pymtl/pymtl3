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

from ..LineTraceParamPass import LineTraceParamPass


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
  A.apply( LineTraceParamPass()      )
  print( A.line_trace() )
  assert A.line_trace() == "verbose"
