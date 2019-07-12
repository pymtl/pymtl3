"""
==========================================================================
RTL2CLWrapper
==========================================================================
Generic wrapper that wraps RTL model into CL.

Author : Yanghui Ou, Yixiao Zhang
  Date : July 9, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

class RTL2CLWrapper( Component ):

  def __init__( s, rtl_model, method_specs ):
    super( RTL2CLWrapper, s ).__init__()

    s.model_name = type( rtl_model ).__name__
    s.method_specs = method_specs

  def construct( s, rtl_model, method_specs ):

    s.model = rtl_model

    # Add adapters
    for method_name, method_spec in s.method_specs.iteritems():
      callee_ifc = NonBlockingCalleeIfc()
      setattr( s, method_name, callee_ifc )
      # print( "[RTL2CLWrapper]: connecting method:", method_name, type( s.model.enq ) )
      s.connect( callee_ifc, getattr( s.model, method_name ) )

  def line_trace( s ):
    return s.model.line_trace()
